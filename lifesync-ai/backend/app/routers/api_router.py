"""백엔드 API 엔드포인트 — 그룹 B 전담.

담당 모듈: agents, voice, services, dashboard, environment
엔드포인트:
  - POST /api/query             (도메인 쿼리 → Orchestrator)
  - POST /api/cascade/preview   (연쇄 효과 미리보기)
  - GET  /api/dashboard/{uid}   (대시보드 게이지)
  - POST /api/feedback          (피드백 수집 + RL 재학습)
  - PUT  /api/state/{uid}       (사용자 상태 업데이트)
  - GET  /api/roadmap/{uid}     (12주 로드맵)
  - GET  /api/auth/kakao/login-url
  - POST /api/auth/kakao/callback
  - GET  /api/auth/me
  - WS   /ws                    (WebSocket)
"""

import json
import logging
import os
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

# --- 서비스 import ---
from backend.agents.orchestrator import Orchestrator
from backend.voice.intent_classifier import IntentClassifier
from backend.voice.tts_responder import TTSResponder
from backend.services.user_state_manager import UserStateManager
from backend.services.feedback_collector import FeedbackCollector
from backend.services.kakao_auth import get_kakao_login_url, kakao_login, verify_token
from backend.risk_engine.timeline_generator import TimelineGenerator
# 공유 서비스 (중복 초기화 방지)
from backend.app.services_init import (
    _safe_init, gauge_calculator, retrain_scheduler, ppo_agent,
)

import re

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Backend API"])

# ============================================================
# 입력 검증 헬퍼
# ============================================================

_USER_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]{1,100}$")


def _validate_user_id(user_id: str) -> str:
    """user_id 형식 검증. 영문/숫자/언더스코어/하이픈만 허용 (1~100자)."""
    if not _USER_ID_PATTERN.match(user_id):
        raise HTTPException(status_code=400, detail="잘못된 user_id 형식 (영문/숫자만)")
    return user_id


# ============================================================
# 서비스 초기화 (그룹 B 전용 — 공유 서비스는 services_init에서)
# ============================================================

orchestrator = _safe_init("Orchestrator", Orchestrator)
intent_classifier = _safe_init("IntentClassifier", IntentClassifier)
tts_responder = _safe_init("TTSResponder", TTSResponder)
state_manager = _safe_init("UserStateManager", UserStateManager)
feedback_collector = _safe_init("FeedbackCollector", FeedbackCollector)
timeline_generator = _safe_init("TimelineGenerator", TimelineGenerator)

# WebSocket 구독자 관리
gauge_subscribers: set[WebSocket] = set()


# ============================================================
# Pydantic 요청 모델
# ============================================================

from enum import Enum as PyEnum

class DomainEnum(str, PyEnum):
    food = "food"
    exercise = "exercise"
    health = "health"
    hobby = "hobby"

class QueryRequest(BaseModel):
    """쿼리 요청 모델 — domain 검증 + 입력 크기 제한."""
    domain: DomainEnum
    action: dict[str, Any] = {}
    user_id: str = "default"

    class Config:
        # action dict 크기 제한 (JSON 직렬화 시 ~10KB)
        max_anystr_length = 5000


class FeedbackRequest(BaseModel):
    """피드백 요청 모델."""
    user_id: str = "default"
    feedback: dict[str, Any]


# ============================================================
# 온보딩 → LifeEnv 초기화 (연결 2)
# ============================================================

class OnboardingRequest(BaseModel):
    """온보딩 데이터 모델."""
    age: str = "30s"
    height: float = 170
    weight: float = 65
    activity: str = "moderate"
    sleep: str = "normal"
    stress: str = "medium"
    goals: list[str] = []


@router.post("/api/onboarding")
async def onboarding(req: OnboardingRequest):
    """온보딩 데이터 → Supabase 저장 + LifeEnv 초기 상태 계산.

    흐름: OnboardingPage → POST → Supabase → 초기 게이지 반환
    """
    # BMI 계산
    height_m = req.height / 100
    bmi = round(req.weight / (height_m ** 2), 1) if height_m > 0 else 22.0

    # 스트레스/수면 → 초기 게이지 매핑
    stress_map = {"low": 20, "medium": 45, "high": 70, "very_high": 90}
    sleep_map = {"night_owl": 55, "normal": 75, "morning": 85}
    activity_map = {"sedentary": 30, "moderate": 55, "active": 75, "very_active": 90}

    initial_gauges = {
        "reactive_oxygen": max(10, 100 - activity_map.get(req.activity, 55)),
        "blood_purity": max(40, 90 - stress_map.get(req.stress, 45) // 3),
        "hair_loss_risk": min(80, stress_map.get(req.stress, 45)),
        "sleep_score": sleep_map.get(req.sleep, 75),
        "stress_level": stress_map.get(req.stress, 45),
        "weekly_achievement": 0,
    }

    # Supabase에 프로필 저장 (가능하면)
    user_id = "default"
    if state_manager:
        try:
            state_manager.update_state(user_id, {
                "bmi": bmi, "weight": req.weight, "height": req.height,
                "stress": initial_gauges["stress_level"],
                "sleep": initial_gauges["sleep_score"],
            })
        except Exception:
            logger.warning("Supabase 프로필 저장 실패 — 로컬 모드")

    return {
        "user_id": user_id,
        "bmi": bmi,
        "bmi_category": "저체중" if bmi < 18.5 else "정상" if bmi < 25 else "과체중" if bmi < 30 else "비만",
        "initial_gauges": initial_gauges,
    }


# ============================================================
# 인증 (카카오 OAuth)
# ============================================================

@router.get("/api/auth/kakao/login-url")
async def kakao_login_url(origin: str = ""):
    """카카오 로그인 URL 반환.

    프론트엔드가 ?origin=https://... 을 전달하면
    해당 origin에 맞는 redirect_uri를 사용합니다.
    """
    return {"url": get_kakao_login_url(origin)}


@router.post("/api/auth/kakao/callback")
async def kakao_callback(data: dict):
    """카카오 인가 코드로 로그인 완료."""
    code = data.get("code")
    origin = data.get("origin", "")
    if not code:
        raise HTTPException(status_code=400, detail="인가 코드 없음")
    try:
        return await kakao_login(code, origin)
    except Exception as e:
        logger.error("카카오 로그인 실패: %s", e)
        raise HTTPException(status_code=401, detail="요청 처리 중 오류가 발생했습니다.")


@router.get("/api/auth/me")
async def auth_me(authorization: str = ""):
    """현재 로그인된 사용자 정보."""
    token = authorization.replace("Bearer ", "") if authorization else ""
    if not token:
        raise HTTPException(status_code=401, detail="토큰 없음")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰")
    return {"user": payload}


# ============================================================
# 도메인 쿼리 & 연쇄 효과
# ============================================================

@router.post("/api/query")
async def query_endpoint(request: QueryRequest) -> dict[str, Any]:
    """도메인 쿼리 → Orchestrator 실행.

    Orchestrator 흐름:
      classify_intent → [도메인 Agent] → merge → cascade → evaluate
    """
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="오케스트레이터 서비스가 초기화되지 않았습니다.")
    try:
        result = orchestrator.run_chain(
            user_id=request.user_id, domain=request.domain, action=request.action,
        )
        # ── 연결: cascade_effects → 게이지 업데이트 계산 ──
        # Orchestrator 결과에 업데이트된 게이지를 추가하여
        # 프론트엔드가 대시보드를 즉시 갱신할 수 있게 한다.
        if gauge_calculator and state_manager:
            try:
                user_state = state_manager.to_dict(request.user_id)
                result["updated_gauges"] = gauge_calculator.calculate_all(user_state)
            except Exception:
                pass
        return result
    except ValueError:
        raise HTTPException(status_code=400, detail="요청 처리 중 오류가 발생했습니다.")
    except Exception as e:
        logger.error("query_endpoint error: %s", e)
        raise HTTPException(status_code=500, detail="요청 처리 중 오류가 발생했습니다.")


@router.post("/api/cascade/preview")
async def cascade_preview(request: QueryRequest) -> dict[str, Any]:
    """연쇄 효과 미리보기."""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="오케스트레이터가 초기화되지 않았습니다.")
    try:
        result = orchestrator.run_chain(
            user_id=request.user_id, domain=request.domain, action=request.action,
        )
    except Exception as e:
        logger.error("cascade_preview error: %s", e)
        raise HTTPException(status_code=500, detail="요청 처리 중 오류가 발생했습니다.")
    return {"domain": request.domain, "cascade_effects": result.get("cascade_effects", {})}


# ============================================================
# 대시보드 & 상태 관리
# ============================================================

def _check_ownership(request, user_id: str) -> None:
    """인증된 사용자와 요청 user_id가 일치하는지 검증 (IDOR 방지).
    개발 환경에서는 검증을 건너뜀.
    """
    if os.getenv("ENV", "production") == "development":
        return
    auth_user = getattr(getattr(request, "state", None), "user", None)
    if auth_user and auth_user.get("user_id") and auth_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="다른 사용자의 데이터에 접근할 수 없습니다.")


@router.get("/api/dashboard/{user_id}")
async def dashboard_endpoint(user_id: str, request: Request = None) -> dict[str, Any]:
    """대시보드 6개 게이지 + 4개 도메인 요약.

    프론트엔드 DashboardPage가 gauges와 domain_summary 모두 사용.
    """
    _validate_user_id(user_id)
    if request:
        _check_ownership(request, user_id)
    if state_manager is None or gauge_calculator is None:
        raise HTTPException(status_code=503, detail="대시보드 서비스가 비활성 상태입니다.")
    user_state = state_manager.to_dict(user_id)
    gauges = gauge_calculator.calculate_all(user_state)

    # 4개 도메인 요약 카드 데이터 생성
    calories = user_state.get("daily_calories", 0)
    exercise_min = user_state.get("exercise_minutes", 0)
    health_status = "양호" if gauges.get("blood_purity", 0) >= 60 else "주의"
    hobby_min = user_state.get("hobby_minutes", 0)

    domain_summary = {
        "food": {"value": f"{int(calories):,} kcal", "sub": "오늘 섭취"},
        "exercise": {"value": f"{int(exercise_min)}분", "sub": "오늘 활동"},
        "health": {"value": health_status, "sub": "종합 상태"},
        "hobby": {"value": f"{int(hobby_min)}분", "sub": "오늘 활동"},
    }

    return {
        "user_id": user_id,
        "gauges": gauges,
        "domain_summary": domain_summary,
        "state": user_state,
    }


@router.put("/api/state/{user_id}")
async def update_state(user_id: str, delta: dict[str, float], request: Request = None) -> dict[str, Any]:
    """사용자 상태 벡터 업데이트."""
    _validate_user_id(user_id)
    if request:
        _check_ownership(request, user_id)
    if state_manager is None:
        raise HTTPException(status_code=503, detail="상태 관리 서비스가 비활성 상태입니다.")
    state_manager.update_state(user_id, delta)
    return {"user_id": user_id, "updated_state": state_manager.to_dict(user_id)}


# ============================================================
# 피드백 & RL 재학습 트리거
# ============================================================

@router.post("/api/feedback")
async def feedback_endpoint(
    request: FeedbackRequest, background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """피드백 수집 → 보상 변환 → 필요 시 백그라운드 RL 재학습."""
    if feedback_collector is None:
        raise HTTPException(status_code=503, detail="피드백 서비스가 비활성 상태입니다.")

    feedback_collector.collect(request.user_id, request.feedback)
    reward = feedback_collector.to_reward(request.feedback)

    retrain_triggered = False
    if retrain_scheduler is not None:
        # 도메인별 만족도 → 보상 가중치 업데이트
        domain_satisfaction = request.feedback.get("domain_scores", {})
        if domain_satisfaction:
            retrain_scheduler.update_user_reward_weights(request.user_id, domain_satisfaction)

        metrics = {
            "avg_reward": reward,
            "feedback_score": request.feedback.get("value", 3.0)
            if isinstance(request.feedback.get("value"), (int, float)) else 3.0,
        }
        if retrain_scheduler.check_trigger(metrics):
            retrain_triggered = True
            background_tasks.add_task(_background_retrain, request.user_id)

    return {"status": "received", "reward": reward, "retrain_triggered": retrain_triggered}


def _background_retrain(user_id: str) -> None:
    """백그라운드 RL 재학습 (피드백 트리거)."""
    if retrain_scheduler is None:
        return
    logger.info("백그라운드 재학습 시작: user=%s", user_id)
    result = retrain_scheduler.schedule_retrain(user_id=user_id)
    logger.info("재학습 결과: %s", result)
    if ppo_agent is not None and result.get("status") == "retrain_completed":
        model_path = f"models/ppo_{user_id}.zip"
        if ppo_agent._model is not None:
            ppo_agent.save(model_path)
            logger.info("학습 모델 저장: %s", model_path)


# ============================================================
# 로드맵
# ============================================================

@router.get("/api/roadmap/{user_id}")
async def roadmap_endpoint(user_id: str) -> dict[str, Any]:
    """12주 로드맵 생성."""
    _validate_user_id(user_id)
    if timeline_generator is None:
        raise HTTPException(status_code=503, detail="로드맵 서비스가 비활성 상태입니다.")
    goals = [
        {"name": "체중 관리", "domain": "exercise", "description": "목표 체중 달성"},
        {"name": "식단 개선", "domain": "food", "description": "균형 잡힌 식단"},
        {"name": "스트레스 관리", "domain": "hobby", "description": "스트레스 해소 루틴"},
    ]
    return {"user_id": user_id, "roadmap": timeline_generator.generate_roadmap(goals, weeks=12)}


# ============================================================
# WebSocket
# ============================================================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket 연결.

    메시지 타입:
      echo      — 에코 테스트
      voice     — 음성 텍스트 → Intent → Orchestrator → 응답
      query     — 도메인 쿼리
      feedback  — 피드백 수집
      subscribe — 게이지 실시간 구독
    """
    ws_user_id = "default"
    if os.getenv("ENV") != "development":
        # 프로덕션: 토큰 필수 — 없으면 연결 거부
        token = websocket.query_params.get("token", "")
        if not token:
            await websocket.close(code=4001, reason="Token required")
            logger.warning("WebSocket 연결 거부: 토큰 없음 (IP=%s)", websocket.client.host if websocket.client else "?")
            return
        payload = verify_token(token)
        if not payload:
            await websocket.close(code=4001, reason="Invalid token")
            logger.warning("WebSocket 인증 실패 (IP=%s)", websocket.client.host if websocket.client else "?")
            return
        ws_user_id = payload.get("user_id", "default")

    await websocket.accept()
    logger.info("WebSocket 연결 성공: user=%s", ws_user_id)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message: dict[str, Any] = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "invalid JSON"})
                continue

            msg_type = message.get("type", "echo")
            data = message.get("data", {})

            if msg_type == "echo":
                await websocket.send_json({"type": "echo", "data": data})

            elif msg_type == "voice":
                await _handle_voice(websocket, data)

            elif msg_type == "query":
                await _handle_query(websocket, data)

            elif msg_type == "feedback":
                await _handle_feedback(websocket, data)

            elif msg_type == "subscribe":
                await _handle_subscribe(websocket, data)

            else:
                await websocket.send_json({"error": f"unknown type: {msg_type}"})

    except WebSocketDisconnect:
        gauge_subscribers.discard(websocket)
        logger.info("WebSocket 연결 종료")


# --- WebSocket 핸들러 (가독성을 위해 분리) ---

async def _handle_voice(ws: WebSocket, data: dict) -> None:
    """음성 텍스트 → Intent 분류 → Orchestrator → 응답."""
    if intent_classifier is None or orchestrator is None:
        await ws.send_json({"type": "error", "data": {"message": "음성 서비스 비활성"}})
        return
    text = data.get("text", "")
    intent = intent_classifier.classify(text)
    domain = intent_classifier.route(intent)
    try:
        result = orchestrator.run_chain(
            user_id=data.get("user_id", "default"), domain=domain, action=data,
        )
        response_text = _format_response(result)
        await ws.send_json({
            "type": "voice_result",
            "data": {"text": response_text, "intent": intent, "result": result},
        })
    except Exception as e:
        logger.error("WS voice error: %s", e)
        await ws.send_json({"type": "error", "data": {"message": "처리 중 오류가 발생했습니다."}})


async def _handle_query(ws: WebSocket, data: dict) -> None:
    """도메인 쿼리 처리."""
    if orchestrator is None:
        await ws.send_json({"type": "error", "data": {"message": "오케스트레이터 비활성"}})
        return
    try:
        result = orchestrator.run_chain(
            user_id=data.get("user_id", "default"),
            domain=data.get("domain", "food"), action=data,
        )
        await ws.send_json({"type": "query_result", "data": result})
    except Exception as e:
        logger.error("WS query error: %s", e)
        await ws.send_json({"type": "error", "data": {"message": "처리 중 오류가 발생했습니다."}})


async def _handle_feedback(ws: WebSocket, data: dict) -> None:
    """피드백 수집."""
    if feedback_collector is None:
        return
    user_id = data.get("user_id", "default")
    feedback_collector.collect(user_id, data)
    reward = feedback_collector.to_reward(data)
    await ws.send_json({"type": "feedback_ack", "data": {"status": "received", "reward": reward}})


async def _handle_subscribe(ws: WebSocket, data: dict) -> None:
    """게이지 실시간 구독."""
    gauge_subscribers.add(ws)
    if state_manager is None or gauge_calculator is None:
        return
    user_id = data.get("user_id", "default")
    user_state = state_manager.to_dict(user_id)
    gauges = gauge_calculator.calculate_all(user_state)
    await ws.send_json({"type": "gauge_update", "data": gauges})


def _format_response(result: dict[str, Any]) -> str:
    """Orchestrator 결과 → 사용자 텍스트 응답."""
    domain = result.get("domain", "")
    agent_result = result.get("result", {})

    formatters = {
        "food": lambda r: f"추천 레시피: {', '.join(x.get('name', '') for x in r.get('recommendations', [])[:3])}",
        "exercise": lambda r: f"추천 운동: {', '.join(x.get('name', '') for x in r.get('exercises', [])[:3])}",
        "health": lambda r: r.get("summary", ""),
        "hobby": lambda r: f"추천 취미: {', '.join(x.get('name', '') for x in r.get('hobbies', [])[:3])}",
    }

    formatter = formatters.get(domain)
    if formatter:
        text = formatter(agent_result)
        if text:
            return text
    return "요청을 처리했습니다."
