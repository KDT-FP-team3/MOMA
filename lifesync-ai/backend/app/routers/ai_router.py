"""AI/ML 엔드포인트 — 그룹 A 전담.

담당 모듈: multimodal, rl_engine, knowledge, risk_engine
엔드포인트:
  - POST /api/photo/upload       (사진 분석)
  - POST /api/food/recognize     (식재료 인식)
  - GET  /api/rl/status          (RL 학습 상태)
  - GET  /api/models/list        (모델 목록)
  - GET  /api/models/{name}/version  (모델 버전)
  - GET  /api/models/{name}/download (모델 다운로드)
  - POST /api/models/upload      (모델 업로드)
  - GET  /api/simulation/actions (시뮬레이션 행동 목록)
  - POST /api/simulation/reset   (시뮬레이션 초기화)
  - POST /api/simulation/step    (시뮬레이션 스텝)
  - POST /api/simulation/predict (시나리오 예측)
  - POST /api/schedule/simulate  (스케줄 시뮬레이션)
  - GET  /api/schedule/activities (활동 유형 목록)
"""

import logging
import os
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

# --- 서비스 import ---
from backend.multimodal.photo_analyzer import PhotoAnalyzer
from backend.multimodal.food_recognizer import FoodRecognizer
from backend.rl_engine.env.life_env import LifeEnv, ACTION_DEFINITIONS
from backend.rl_engine.reward_cross_domain import CrossDomainReward
from backend.rl_engine.schedule_simulator import ScheduleSimulator
from backend.rl_engine.retrain_scheduler import RetrainScheduler
from backend.rl_engine.ppo_agent import PPOAgent
from backend.services.model_registry import ModelRegistry
from backend.dashboard.gauge_calculator import GaugeCalculator

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI/ML"])


# ============================================================
# 서비스 초기화 (그룹 A 담당 서비스만)
# ============================================================

def _safe_init(name: str, factory):
    """서비스 안전 초기화. 실패 시 None 반환 + 로그."""
    try:
        instance = factory()
        logger.info("[AI Router] 서비스 초기화 성공: %s", name)
        return instance
    except Exception:
        logger.exception("[AI Router] 서비스 초기화 실패 (비활성): %s", name)
        return None


photo_analyzer = _safe_init("PhotoAnalyzer", PhotoAnalyzer)
food_recognizer = _safe_init("FoodRecognizer", FoodRecognizer)
reward_calculator = _safe_init("CrossDomainReward", CrossDomainReward)
schedule_simulator = _safe_init("ScheduleSimulator", ScheduleSimulator)
retrain_scheduler = _safe_init("RetrainScheduler", RetrainScheduler)
ppo_agent = _safe_init("PPOAgent", PPOAgent)
model_registry = _safe_init("ModelRegistry", ModelRegistry)
gauge_calculator = _safe_init("GaugeCalculator", GaugeCalculator)


# ============================================================
# 상수 & 세션 관리
# ============================================================

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024      # 10MB
MODEL_UPLOAD_MAX_SIZE = 100 * 1024 * 1024  # 100MB

# RL 시뮬레이션 세션 (메모리 내 관리)
simulation_sessions: dict[str, Any] = {}


# ============================================================
# Pydantic 요청 모델
# ============================================================

class SimulationRequest(BaseModel):
    """시뮬레이션 행동 요청."""
    session_id: str = "default"
    action_id: int


class ScheduleSimRequest(BaseModel):
    """스케줄 시뮬레이션 요청."""
    schedule: list[dict[str, Any]]
    days: int = 30
    initial_state: dict[str, Any] | None = None


# ============================================================
# 사진 분석 / 식재료 인식
# ============================================================

@router.post("/api/photo/upload")
async def photo_upload(file: UploadFile = File(...)) -> dict[str, Any]:
    """사진 업로드 → CLIP 임베딩 → Top-5 유사 분석."""
    if photo_analyzer is None:
        raise HTTPException(status_code=503, detail="사진 분석 서비스가 비활성 상태입니다.")
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="허용되지 않는 파일 형식입니다.")

    image_bytes = await file.read()
    if len(image_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="파일 크기 초과 (최대 10MB)")

    top_k = photo_analyzer.get_top_k_similar(image_bytes, k=5)
    face = photo_analyzer.analyze_face(image_bytes)
    body = photo_analyzer.analyze_body(image_bytes)

    return {
        "filename": file.filename,
        "top_5": top_k,
        "face_analysis": face,
        "body_analysis": {
            "body_type": body.get("body_type_estimate", ""),
            "posture_score": body.get("posture_score", 0),
        },
    }


@router.post("/api/food/recognize")
async def food_recognize(file: UploadFile = File(...)) -> dict[str, Any]:
    """YOLO 기반 식재료 인식."""
    if food_recognizer is None:
        raise HTTPException(status_code=503, detail="식재료 인식 서비스가 비활성 상태입니다.")
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="허용되지 않는 파일 형식입니다.")

    image_bytes = await file.read()
    if len(image_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="파일 크기 초과 (최대 10MB)")

    detections = food_recognizer.detect(image_bytes)
    labels = food_recognizer.classify(image_bytes)
    return {"filename": file.filename, "detections": detections, "labels": labels, "count": len(detections)}


# ============================================================
# RL 시뮬레이션 (건강 시뮬레이터)
# ============================================================

@router.get("/api/simulation/actions")
async def get_simulation_actions() -> dict[str, Any]:
    """시뮬레이션 가능한 행동 목록 반환."""
    return {"actions": ACTION_DEFINITIONS}


@router.post("/api/simulation/reset")
async def simulation_reset(session_id: str = "default") -> dict[str, Any]:
    """시뮬레이션 환경 초기화 — 가상 인물 생성."""
    try:
        env = LifeEnv()
        obs, info = env.reset()
        simulation_sessions[session_id] = env
        state = _obs_to_health_state(obs)
    except Exception as e:
        logger.warning("LifeEnv 초기화 실패 (폴백 사용): %s", e)
        state = _default_health_state()
        simulation_sessions[session_id] = None

    gauges = gauge_calculator.calculate_all(state) if gauge_calculator else {}
    return {
        "session_id": session_id,
        "step": 0,
        "health_state": state,
        "gauges": gauges,
        "message": "가상 인물이 생성되었습니다. 행동을 선택해주세요.",
    }


@router.post("/api/simulation/step")
async def simulation_step(request: SimulationRequest) -> dict[str, Any]:
    """시뮬레이션 한 스텝 실행 — 행동에 따른 건강 변화 계산."""
    action_id = max(0, min(9, request.action_id))
    action_def = ACTION_DEFINITIONS[action_id]
    env = simulation_sessions.get(request.session_id)

    # --- LifeEnv 사용 가능한 경우 ---
    if env is not None:
        try:
            obs, reward, terminated, truncated, info = env.step(action_id)
            state = _obs_to_health_state(obs)
            step_num = info["step"]
        except Exception as e:
            logger.warning("LifeEnv step 실패 (폴백): %s", e)
            env = None

    # --- 폴백 시뮬레이션 (gymnasium 없을 때) ---
    if env is None:
        state, step_num, reward, terminated = _fallback_step(request.session_id, action_id)

    gauges = gauge_calculator.calculate_all(state) if gauge_calculator else {}
    cascade_msg = _build_cascade_message(action_def, state, reward)

    return {
        "session_id": request.session_id,
        "step": step_num,
        "action": action_def,
        "reward": round(reward, 2),
        "health_state": state,
        "gauges": gauges,
        "cascade_message": cascade_msg,
        "terminated": terminated,
        "week": (step_num - 1) // 7 + 1,
        "day": (step_num - 1) % 7 + 1,
    }


@router.post("/api/simulation/predict")
async def simulation_predict(session_id: str = "default") -> dict[str, Any]:
    """현재 상태에서 10가지 행동의 결과를 미리 예측."""
    env = simulation_sessions.get(session_id)
    if env is None:
        return {"error": "세션을 먼저 시작해주세요. POST /api/simulation/reset"}

    current_obs = env._state.copy()
    predictions: list[dict[str, Any]] = []

    for action_def in ACTION_DEFINITIONS:
        temp_env = LifeEnv()
        temp_env.reset()
        temp_env._state = current_obs.copy()
        temp_env._step_count = env._step_count

        obs, reward, _, _, _ = temp_env.step(action_def["id"])
        future_state = _obs_to_health_state(obs)
        future_gauges = gauge_calculator.calculate_all(future_state) if gauge_calculator else {}

        predictions.append({
            "action": action_def,
            "reward": round(reward, 2),
            "predicted_state": future_state,
            "predicted_gauges": future_gauges,
        })

    predictions.sort(key=lambda x: x["reward"], reverse=True)
    return {"session_id": session_id, "current_step": env._step_count, "predictions": predictions}


# ============================================================
# 스케줄 시뮬레이션
# ============================================================

@router.post("/api/schedule/simulate")
async def schedule_simulate(request: ScheduleSimRequest) -> dict[str, Any]:
    """24시간 스케줄 기반 장기 시뮬레이션."""
    if schedule_simulator is None:
        raise HTTPException(status_code=503, detail="시뮬레이터 서비스가 초기화되지 않았습니다.")
    try:
        return schedule_simulator.simulate(
            schedule=request.schedule, days=request.days, initial_state=request.initial_state,
        )
    except Exception as e:
        logger.exception("schedule_simulate 에러")
        raise HTTPException(status_code=500, detail="요청 처리 중 오류가 발생했습니다.")


@router.get("/api/schedule/activities")
async def get_schedule_activities() -> dict[str, Any]:
    """스케줄에 사용 가능한 활동 유형 목록."""
    return {"activities": [
        {"key": "sleep",             "label": "수면",          "emoji": "😴", "color": "#748ffc", "category": "생활"},
        {"key": "meal_healthy",      "label": "건강한 식사",    "emoji": "🥗", "color": "#51cf66", "category": "식사"},
        {"key": "meal_normal",       "label": "일반 식사",      "emoji": "🍚", "color": "#ff922b", "category": "식사"},
        {"key": "meal_unhealthy",    "label": "불건강한 식사",   "emoji": "🍔", "color": "#ff6b6b", "category": "식사"},
        {"key": "night_snack",       "label": "야식",          "emoji": "🍜", "color": "#e64980", "category": "식사"},
        {"key": "exercise_cardio",   "label": "유산소 운동",    "emoji": "🏃", "color": "#339af0", "category": "운동"},
        {"key": "exercise_strength", "label": "근력 운동",      "emoji": "🏋️", "color": "#5c7cfa", "category": "운동"},
        {"key": "work",             "label": "업무/공부",       "emoji": "💼", "color": "#868e96", "category": "생활"},
        {"key": "hobby",            "label": "취미",           "emoji": "🎸", "color": "#cc5de8", "category": "여가"},
        {"key": "rest",             "label": "휴식",           "emoji": "☕", "color": "#20c997", "category": "여가"},
        {"key": "commute",          "label": "통근/이동",       "emoji": "🚌", "color": "#adb5bd", "category": "생활"},
        {"key": "other",            "label": "기타",           "emoji": "📌", "color": "#ced4da", "category": "기타"},
    ]}


# ============================================================
# 모델 동기화 API (오프라인 지원)
# ============================================================

@router.get("/api/models/list")
async def list_models() -> dict[str, Any]:
    """등록된 모델 목록."""
    if model_registry is None:
        return {"models": {}}
    return {"models": model_registry.list_models()}


@router.get("/api/models/{model_name}/version")
async def model_version(model_name: str) -> dict[str, Any]:
    """모델 최신 버전 정보 (클라이언트 동기화 체크용)."""
    if model_registry is None:
        return {"model_name": model_name, "version": 0, "available": False}
    return model_registry.get_latest_version(model_name)


@router.get("/api/models/{model_name}/download")
async def download_model_weights(model_name: str):
    """모델 가중치 파일 다운로드."""
    if model_registry is None:
        raise HTTPException(status_code=503, detail="모델 레지스트리 비활성")
    local_path = model_registry.download_model(model_name)
    if not local_path or not os.path.exists(local_path):
        raise HTTPException(status_code=404, detail=f"모델 '{model_name}' 파일 없음")
    from starlette.responses import FileResponse
    return FileResponse(local_path, filename=os.path.basename(local_path), media_type="application/octet-stream")


@router.post("/api/models/upload")
async def upload_model_endpoint(model_name: str, file: UploadFile = File(...)) -> dict[str, Any]:
    """모델 업로드 (로컬 GPU 학습 → S3 + 버전 등록)."""
    if model_registry is None:
        raise HTTPException(status_code=503, detail="모델 레지스트리 비활성")
    safe_model_name = os.path.basename(model_name)
    safe_filename = os.path.basename(file.filename or "model.zip")
    if not safe_model_name or safe_model_name.startswith("."):
        raise HTTPException(status_code=400, detail="잘못된 모델 이름")

    content = await file.read()
    if len(content) > MODEL_UPLOAD_MAX_SIZE:
        raise HTTPException(status_code=413, detail="파일 크기 초과 (최대 100MB)")

    save_dir = os.path.join("models", safe_model_name)
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, safe_filename)
    with open(save_path, "wb") as f:
        f.write(content)

    return model_registry.upload_model(safe_model_name, save_path)


@router.get("/api/rl/status")
async def rl_status() -> dict[str, Any]:
    """RL 학습 상태 조회."""
    import time
    status: dict[str, Any] = {"retrain_scheduler": retrain_scheduler is not None}
    if retrain_scheduler is not None:
        status["avg_confidence"] = retrain_scheduler.get_average_confidence()
        status["recent_rewards_count"] = len(retrain_scheduler._recent_rewards)
        status["last_retrain_elapsed_hours"] = round(
            (time.time() - retrain_scheduler._last_retrain_time) / 3600, 1
        )
    if ppo_agent is not None:
        status["ppo_model_loaded"] = ppo_agent._model is not None
    return status


# ============================================================
# 헬퍼 함수
# ============================================================

def _obs_to_health_state(obs) -> dict[str, Any]:
    """관측 벡터(numpy) → 건강 상태 딕셔너리."""
    return {
        "calorie_intake": round(float(obs[0]), 1),
        "calorie_burned": round(float(obs[1]), 1),
        "sleep_score": round(float(obs[2]), 1),
        "stress_level": round(float(obs[3]), 1),
        "weight_kg": round(float(obs[4]), 2),
        "bmi": round(float(obs[5]), 1),
        "blood_pressure_sys": round(float(obs[6]), 0),
        "blood_pressure_dia": round(float(obs[7]), 0),
        "mood_score": round(float(obs[8]), 1),
        "weekly_achievement": round(float(obs[9]), 3),
    }


def _default_health_state() -> dict[str, Any]:
    """LifeEnv 없을 때 기본 건강 상태."""
    return {
        "calorie_intake": 2000.0, "calorie_burned": 200.0,
        "sleep_score": 60.0, "stress_level": 50.0,
        "weight_kg": 75.0, "bmi": 25.0,
        "blood_pressure_sys": 120.0, "blood_pressure_dia": 80.0,
        "mood_score": 50.0, "weekly_achievement": 0.0,
    }


# 폴백 시뮬레이션 효과 테이블
_FALLBACK_EFFECTS = {
    0: {"mood_score": 2, "weight_kg": -0.02},                          # healthy_meal
    1: {"mood_score": 5, "weight_kg": 0.07, "stress_level": 2},        # unhealthy_meal
    2: {"mood_score": -5, "stress_level": 5},                           # skip_meal
    3: {"sleep_score": 3, "stress_level": -5, "weight_kg": -0.05},      # cardio
    4: {"sleep_score": 2, "stress_level": -3},                          # strength
    5: {"stress_level": 3},                                             # skip_exercise
    6: {"mood_score": 3, "stress_level": -5},                           # health_check
    7: {"sleep_score": 10, "stress_level": -5},                         # sleep_optimize
    8: {"stress_level": -8, "mood_score": 5},                           # hobby
    9: {"sleep_score": 5, "stress_level": -2},                          # rest
}


def _fallback_step(session_id: str, action_id: int):
    """gymnasium 없을 때 간단한 폴백 시뮬레이션."""
    prev = simulation_sessions.get(f"{session_id}_state", _default_health_state())
    step_num = simulation_sessions.get(f"{session_id}_step", 0) + 1

    deltas = _FALLBACK_EFFECTS.get(action_id, {})
    state = {**prev}
    for key, value in deltas.items():
        if key == "weight_kg":
            state[key] = state.get(key, 75) + value
        else:
            state[key] = max(0, min(100, state.get(key, 50) + value))
    state["bmi"] = round(state["weight_kg"] / (1.75 ** 2), 1)

    simulation_sessions[f"{session_id}_state"] = state
    simulation_sessions[f"{session_id}_step"] = step_num
    reward = sum(deltas.values()) * 0.3
    terminated = step_num >= 84

    return state, step_num, reward, terminated


def _build_cascade_message(
    action_def: dict[str, Any], state: dict[str, Any], reward: float
) -> dict[str, Any]:
    """행동 → 연쇄 효과 메시지 생성.

    각 행동에 대해 어떤 도메인에 어떤 영향이 있는지 설명한다.
    severity: positive(보상≥0), medium(-3<보상<0), high(보상≤-3)
    """
    name = action_def["name"]
    effects: list[dict[str, str]] = []

    cascade_map = {
        "unhealthy_meal": [
            ("health", f"체중 +0.07kg → BMI {state['bmi']}"),
            ("health", "스트레스 +2 (죄책감)"),
            ("exercise", "추가 운동 필요"),
        ],
        "healthy_meal": [
            ("health", "체중 미세 감소"),
            ("health", "기분 +2"),
        ],
        "skip_meal": [
            ("health", "기분 -5, 스트레스 +5"),
            ("exercise", "운동 에너지 부족"),
        ],
        "cardio_exercise": [
            ("health", f"수면 점수 → {state['sleep_score']}"),
            ("health", f"스트레스 → {state['stress_level']}"),
            ("food", "단백질 보충 필요"),
        ],
        "strength_exercise": [
            ("health", "근력 향상"),
            ("food", "고단백 식단 권장"),
        ],
        "skip_exercise": [
            ("health", "스트레스 +3"),
        ],
        "health_check": [
            ("health", "불안감 감소, 기분 +3"),
        ],
        "sleep_optimize": [
            ("health", f"수면 크게 개선 → {state['sleep_score']}"),
            ("exercise", "운동 효율 증가"),
        ],
        "hobby_activity": [
            ("health", f"스트레스 크게 감소 → {state['stress_level']}"),
            ("food", "폭식 충동 -40%"),
            ("exercise", "운동 동기부여 증가"),
        ],
    }

    for domain, impact in cascade_map.get(name, []):
        effects.append({"domain": domain, "impact": impact})

    return {
        "action_name": action_def["description"],
        "domain": action_def["domain"],
        "reward": round(reward, 2),
        "severity": "positive" if reward >= 0 else ("medium" if reward > -3 else "high"),
        "effects": effects,
    }
