"""FastAPI 애플리케이션 진입점 — WebSocket 및 REST API."""

from dotenv import load_dotenv
load_dotenv(encoding="utf-8")

import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.agents.orchestrator import Orchestrator
from backend.voice.intent_classifier import IntentClassifier
from backend.voice.tts_responder import TTSResponder
from backend.services.user_state_manager import UserStateManager
from backend.services.feedback_collector import FeedbackCollector
from backend.dashboard.gauge_calculator import GaugeCalculator
from backend.multimodal.photo_analyzer import PhotoAnalyzer
from backend.risk_engine.timeline_generator import TimelineGenerator
from backend.risk_engine.night_meal_penalty import NightMealPenalty
from backend.multimodal.food_recognizer import FoodRecognizer
from backend.rl_engine.env.life_env import LifeEnv, ACTION_DEFINITIONS
from backend.rl_engine.reward_cross_domain import CrossDomainReward
from backend.rl_engine.schedule_simulator import ScheduleSimulator
from backend.rl_engine.retrain_scheduler import RetrainScheduler
from backend.rl_engine.ppo_agent import PPOAgent
from backend.services.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 이벤트 관리."""
    logger.info("LifeSync AI 서버 시작")
    yield
    # 종료 시 DB 연결 풀 정리
    if state_manager is not None:
        state_manager.close()
    logger.info("LifeSync AI 서버 종료")


app = FastAPI(title="LifeSync AI", version="0.1.0", lifespan=lifespan)

# --- 보안 미들웨어 ---
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """보안 응답 헤더 자동 추가."""

    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if os.getenv("ENV") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# CORS — 허용 도메인 제한
ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:8000,capacitor://localhost,http://localhost"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# 파일 업로드 보안 상수
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# --- 서비스 초기화 (개별 실패 허용) ---
def _safe_init(name: str, factory):
    """서비스를 안전하게 초기화. 실패 시 None 반환."""
    try:
        instance = factory()
        logger.info("서비스 초기화 성공: %s", name)
        return instance
    except Exception:
        logger.exception("서비스 초기화 실패 (비활성): %s", name)
        return None

orchestrator = _safe_init("Orchestrator", Orchestrator)
intent_classifier = _safe_init("IntentClassifier", IntentClassifier)
tts_responder = _safe_init("TTSResponder", TTSResponder)
state_manager = _safe_init("UserStateManager", UserStateManager)
feedback_collector = _safe_init("FeedbackCollector", FeedbackCollector)
gauge_calculator = _safe_init("GaugeCalculator", GaugeCalculator)
photo_analyzer = _safe_init("PhotoAnalyzer", PhotoAnalyzer)
timeline_generator = _safe_init("TimelineGenerator", TimelineGenerator)
night_meal_penalty = _safe_init("NightMealPenalty", NightMealPenalty)
food_recognizer = _safe_init("FoodRecognizer", FoodRecognizer)
reward_calculator = _safe_init("CrossDomainReward", CrossDomainReward)
schedule_simulator = _safe_init("ScheduleSimulator", ScheduleSimulator)
retrain_scheduler = _safe_init("RetrainScheduler", RetrainScheduler)
ppo_agent = _safe_init("PPOAgent", PPOAgent)
model_registry = _safe_init("ModelRegistry", ModelRegistry)

# --- RL 시뮬레이션 세션 관리 ---
simulation_sessions: dict[str, LifeEnv] = {}

# --- WebSocket 구독 클라이언트 관리 ---
gauge_subscribers: set[WebSocket] = set()


# --- Pydantic 모델 ---
class QueryRequest(BaseModel):
    """쿼리 요청 모델."""
    domain: str
    action: dict[str, Any] = {}
    user_id: str = "default"


class FeedbackRequest(BaseModel):
    """피드백 요청 모델."""
    user_id: str = "default"
    feedback: dict[str, Any]


# --- JWT 인증 미들웨어 ---
from backend.services.kakao_auth import get_kakao_login_url, kakao_login, verify_token
from starlette.requests import Request

# 인증 불필요 경로
PUBLIC_PATHS = {
    "/health", "/docs", "/openapi.json", "/redoc",
    "/api/auth/kakao/login-url", "/api/auth/kakao/callback",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """JWT 토큰 검증 미들웨어.

    PUBLIC_PATHS와 OPTIONS 요청은 인증 없이 통과.
    나머지는 Authorization 헤더의 Bearer 토큰을 검증.
    개발 환경(ENV != production)에서는 인증을 선택적으로 적용.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # 공개 경로 및 OPTIONS(CORS preflight) 통과
        if path in PUBLIC_PATHS or request.method == "OPTIONS":
            return await call_next(request)
        # WebSocket은 별도 처리
        if path.startswith("/ws"):
            return await call_next(request)
        # 개발 환경(로컬)에서만 인증 선택적 — ENV=development 명시 필요
        if os.getenv("ENV") == "development":
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
        if not token:
            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={"detail": "인증 토큰이 필요합니다."},
            )
        payload = verify_token(token)
        if not payload:
            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={"detail": "유효하지 않은 토큰입니다."},
            )
        # 요청에 사용자 정보 주입
        request.state.user = payload
        return await call_next(request)


app.add_middleware(AuthMiddleware)

# --- Rate Limiting ---
_rate_limit_store: dict[str, list[float]] = {}
RATE_LIMIT_MAX = 60  # 분당 최대 요청 수
RATE_LIMIT_WINDOW = 60  # 초


class RateLimitMiddleware(BaseHTTPMiddleware):
    """IP 기반 Rate Limiting 미들웨어 (분당 60회)."""

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = __import__("time").time()

        if client_ip not in _rate_limit_store:
            _rate_limit_store[client_ip] = []

        # 윈도우 밖 기록 제거
        _rate_limit_store[client_ip] = [
            t for t in _rate_limit_store[client_ip]
            if now - t < RATE_LIMIT_WINDOW
        ]

        if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_MAX:
            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"detail": "요청 한도 초과. 잠시 후 다시 시도하세요."},
            )

        _rate_limit_store[client_ip].append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_MAX)
        response.headers["X-RateLimit-Remaining"] = str(
            RATE_LIMIT_MAX - len(_rate_limit_store[client_ip])
        )
        return response


app.add_middleware(RateLimitMiddleware)


@app.get("/api/auth/kakao/login-url")
async def kakao_login_url():
    """카카오 로그인 URL 반환."""
    return {"url": get_kakao_login_url()}


@app.post("/api/auth/kakao/callback")
async def kakao_callback(data: dict):
    """카카오 인가 코드로 로그인 완료."""
    code = data.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="인가 코드 없음")
    try:
        result = await kakao_login(code)
        return result
    except Exception as e:
        logger.error("카카오 로그인 실패: %s", e)
        raise HTTPException(status_code=401, detail="요청 처리 중 오류가 발생했습니다.")


@app.get("/api/auth/me")
async def auth_me(authorization: str = ""):
    """현재 로그인된 사용자 정보."""
    token = authorization.replace("Bearer ", "") if authorization else ""
    if not token:
        raise HTTPException(status_code=401, detail="토큰 없음")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰")
    return {"user": payload}


# --- REST 엔드포인트 ---
@app.get("/health")
async def health_check() -> dict[str, str]:
    """헬스체크 엔드포인트."""
    return {"status": "ok"}


@app.post("/api/query")
async def query_endpoint(request: QueryRequest) -> dict[str, Any]:
    """도메인 쿼리 엔드포인트.

    Args:
        request: 쿼리 요청 (domain, action, user_id).

    Returns:
        오케스트레이터 실행 결과.
    """
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="오케스트레이터 서비스가 초기화되지 않았습니다.")
    try:
        result = orchestrator.run_chain(
            user_id=request.user_id,
            domain=request.domain,
            action=request.action,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail="요청 처리 중 오류가 발생했습니다.")
    except Exception as e:
        logger.error("query_endpoint error: %s", e)
        raise HTTPException(status_code=500, detail="요청 처리 중 오류가 발생했습니다.")


@app.post("/api/photo/upload")
async def photo_upload(file: UploadFile = File(...)) -> dict[str, Any]:
    """사진 업로드 및 분석 엔드포인트.

    Args:
        file: 업로드된 이미지 파일.

    Returns:
        Top-5 분석 결과.
    """
    if photo_analyzer is None:
        raise HTTPException(status_code=503, detail="사진 분석 서비스가 비활성 상태입니다.")
    # 파일 타입 검증
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="허용되지 않는 파일 형식입니다.")
    image_bytes = await file.read()
    # 파일 크기 검증
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


@app.get("/api/dashboard/{user_id}")
async def dashboard_endpoint(user_id: str) -> dict[str, Any]:
    """대시보드 게이지 데이터 엔드포인트.

    Args:
        user_id: 사용자 식별자.

    Returns:
        6개 게이지 점수.
    """
    if state_manager is None or gauge_calculator is None:
        raise HTTPException(status_code=503, detail="대시보드 서비스가 비활성 상태입니다.")
    user_state = state_manager.to_dict(user_id)
    gauges = gauge_calculator.calculate_all(user_state)
    return {"user_id": user_id, "gauges": gauges, "state": user_state}


@app.post("/api/feedback")
async def feedback_endpoint(
    request: FeedbackRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """피드백 수집 + RL 재학습 트리거."""
    if feedback_collector is None:
        raise HTTPException(status_code=503, detail="피드백 서비스가 비활성 상태입니다.")
    feedback_collector.collect(request.user_id, request.feedback)
    reward = feedback_collector.to_reward(request.feedback)

    # RL 피드백 루프: 트리거 조건 확인 → 백그라운드 재학습
    retrain_triggered = False
    if retrain_scheduler is not None:
        # 사용자별 보상 가중치 업데이트
        domain_satisfaction = request.feedback.get("domain_scores", {})
        if domain_satisfaction:
            retrain_scheduler.update_user_reward_weights(
                request.user_id, domain_satisfaction
            )

        metrics = {
            "avg_reward": reward,
            "feedback_score": request.feedback.get("value", 3.0)
            if isinstance(request.feedback.get("value"), (int, float))
            else 3.0,
        }
        if retrain_scheduler.check_trigger(metrics):
            retrain_triggered = True
            background_tasks.add_task(
                _background_retrain, request.user_id
            )

    return {
        "status": "received",
        "reward": reward,
        "retrain_triggered": retrain_triggered,
    }


def _background_retrain(user_id: str) -> None:
    """백그라운드 RL 재학습."""
    if retrain_scheduler is None:
        return
    logger.info("백그라운드 재학습 시작: user=%s", user_id)
    result = retrain_scheduler.schedule_retrain(user_id=user_id)
    logger.info("재학습 결과: %s", result)

    # 학습된 모델 로드
    if ppo_agent is not None and result.get("status") == "retrain_completed":
        model_path = f"models/ppo_{user_id}.zip"
        if ppo_agent._model is not None:
            ppo_agent.save(model_path)
            logger.info("학습 모델 저장: %s", model_path)


@app.get("/api/rl/status")
async def rl_status() -> dict[str, Any]:
    """RL 학습 상태 조회."""
    status: dict[str, Any] = {"retrain_scheduler": retrain_scheduler is not None}
    if retrain_scheduler is not None:
        status["avg_confidence"] = retrain_scheduler.get_average_confidence()
        status["recent_rewards_count"] = len(retrain_scheduler._recent_rewards)
        status["last_retrain_elapsed_hours"] = round(
            (__import__("time").time() - retrain_scheduler._last_retrain_time) / 3600, 1
        )
    if ppo_agent is not None:
        status["ppo_model_loaded"] = ppo_agent._model is not None
    return status


# --- 모델 동기화 API (클라이언트 오프라인 지원) ---


@app.get("/api/models/list")
async def list_models() -> dict[str, Any]:
    """등록된 모델 목록 조회."""
    if model_registry is None:
        return {"models": {}}
    return {"models": model_registry.list_models()}


@app.get("/api/models/{model_name}/version")
async def model_version(model_name: str) -> dict[str, Any]:
    """모델 최신 버전 정보 (클라이언트 동기화 체크용).

    클라이언트는 로컬 버전과 비교하여 업데이트 필요 여부를 판단한다.
    """
    if model_registry is None:
        return {"model_name": model_name, "version": 0, "available": False}
    return model_registry.get_latest_version(model_name)


@app.get("/api/models/{model_name}/download")
async def download_model_weights(model_name: str):
    """모델 가중치 파일 다운로드 (클라이언트 오프라인용)."""
    if model_registry is None:
        raise HTTPException(status_code=503, detail="모델 레지스트리 비활성")

    local_path = model_registry.download_model(model_name)
    if not local_path or not os.path.exists(local_path):
        raise HTTPException(status_code=404, detail=f"모델 '{model_name}' 파일 없음")

    from starlette.responses import FileResponse
    return FileResponse(
        local_path,
        filename=os.path.basename(local_path),
        media_type="application/octet-stream",
    )


MODEL_UPLOAD_MAX_SIZE = 100 * 1024 * 1024  # 100MB


@app.post("/api/models/upload")
async def upload_model_endpoint(
    model_name: str,
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """모델 업로드 (로컬 GPU 학습 결과 → S3 + 버전 등록)."""
    if model_registry is None:
        raise HTTPException(status_code=503, detail="모델 레지스트리 비활성")

    # 경로 트래버설 방지: 파일명/모델명 안전화
    safe_model_name = os.path.basename(model_name)
    safe_filename = os.path.basename(file.filename or "model.zip")
    if not safe_model_name or safe_model_name.startswith("."):
        raise HTTPException(status_code=400, detail="잘못된 모델 이름")

    content = await file.read()

    # 파일 크기 검증
    if len(content) > MODEL_UPLOAD_MAX_SIZE:
        raise HTTPException(status_code=413, detail="파일 크기 초과 (최대 100MB)")

    save_dir = os.path.join("models", safe_model_name)
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, safe_filename)

    with open(save_path, "wb") as f:
        f.write(content)

    result = model_registry.upload_model(safe_model_name, save_path)
    return result


@app.get("/api/roadmap/{user_id}")
async def roadmap_endpoint(user_id: str) -> dict[str, Any]:
    """12주 로드맵 엔드포인트."""
    # 기본 목표 (사용자 선택에 따라 동적 생성 가능)
    goals = [
        {"name": "체중 관리", "domain": "exercise", "description": "목표 체중 달성"},
        {"name": "식단 개선", "domain": "food", "description": "균형 잡힌 식단"},
        {"name": "스트레스 관리", "domain": "hobby", "description": "스트레스 해소 루틴"},
    ]
    roadmap = timeline_generator.generate_roadmap(goals, weeks=12)
    return {"user_id": user_id, "roadmap": roadmap}


@app.post("/api/cascade/preview")
async def cascade_preview(request: QueryRequest) -> dict[str, Any]:
    """연쇄 효과 미리보기 엔드포인트."""
    try:
        result = orchestrator.run_chain(
            user_id=request.user_id,
            domain=request.domain,
            action=request.action,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="요청 처리 중 오류가 발생했습니다.")
    except Exception as e:
        logger.error("cascade_preview error: %s", e)
        raise HTTPException(status_code=500, detail="요청 처리 중 오류가 발생했습니다.")
    return {
        "domain": request.domain,
        "cascade_effects": result.get("cascade_effects", {}),
    }


@app.put("/api/state/{user_id}")
async def update_state(
    user_id: str, delta: dict[str, float]
) -> dict[str, Any]:
    """사용자 상태 업데이트 엔드포인트."""
    state = state_manager.update_state(user_id, delta)
    return {"user_id": user_id, "updated_state": state_manager.to_dict(user_id)}


# --- RL 시뮬레이션 API ---
class SimulationRequest(BaseModel):
    """시뮬레이션 행동 요청."""
    session_id: str = "default"
    action_id: int


@app.get("/api/simulation/actions")
async def get_simulation_actions() -> dict[str, Any]:
    """시뮬레이션 가능한 행동 목록."""
    return {"actions": ACTION_DEFINITIONS}


@app.post("/api/simulation/reset")
async def simulation_reset(session_id: str = "default") -> dict[str, Any]:
    """시뮬레이션 환경 초기화 — 가상 인물 생성.

    Returns:
        초기 건강 상태 (40차원 벡터의 주요 지표).
    """
    try:
        env = LifeEnv()
        obs, info = env.reset()
        simulation_sessions[session_id] = env
        state = _obs_to_health_state(obs)
    except Exception as e:
        logger.warning("LifeEnv 초기화 실패 (폴백 사용): %s", e)
        # gymnasium 없을 때 폴백 시뮬레이션
        state = {
            "calorie_intake": 2000.0, "calorie_burned": 200.0,
            "sleep_score": 60.0, "stress_level": 50.0,
            "weight_kg": 75.0, "bmi": 25.0,
            "blood_pressure_sys": 120.0, "blood_pressure_dia": 80.0,
            "mood_score": 50.0, "weekly_achievement": 0.0,
        }
        simulation_sessions[session_id] = None

    gauges = gauge_calculator.calculate_all(state)

    return {
        "session_id": session_id,
        "step": 0,
        "health_state": state,
        "gauges": gauges,
        "message": "가상 인물이 생성되었습니다. 행동을 선택해주세요.",
    }


@app.post("/api/simulation/step")
async def simulation_step(request: SimulationRequest) -> dict[str, Any]:
    """시뮬레이션 한 스텝 실행 — 선택에 따른 건강 변화.

    Returns:
        변화된 건강 상태, 보상, 연쇄 효과.
    """
    action_id = max(0, min(9, request.action_id))
    action_def = ACTION_DEFINITIONS[action_id]

    env = simulation_sessions.get(request.session_id)

    # LifeEnv 사용 가능한 경우
    if env is not None:
        try:
            obs, reward, terminated, truncated, info = env.step(action_id)
            state = _obs_to_health_state(obs)
            step_num = info["step"]
        except Exception as e:
            logger.warning("LifeEnv step 실패 (폴백 사용): %s", e)
            env = None

    # 폴백 시뮬레이션 (gymnasium 없을 때)
    if env is None:
        prev = simulation_sessions.get(f"{request.session_id}_state", {
            "calorie_intake": 2000.0, "calorie_burned": 200.0,
            "sleep_score": 60.0, "stress_level": 50.0,
            "weight_kg": 75.0, "bmi": 25.0,
            "blood_pressure_sys": 120.0, "blood_pressure_dia": 80.0,
            "mood_score": 50.0, "weekly_achievement": 0.0,
        })
        step_num = simulation_sessions.get(f"{request.session_id}_step", 0) + 1
        # 간단한 효과 적용
        effects = {
            0: {"mood_score": 2, "weight_kg": -0.02},        # healthy_meal
            1: {"mood_score": 5, "weight_kg": 0.07, "stress_level": 2},  # unhealthy
            2: {"mood_score": -5, "stress_level": 5},         # skip_meal
            3: {"sleep_score": 3, "stress_level": -5, "weight_kg": -0.05},  # cardio
            4: {"sleep_score": 2, "stress_level": -3},         # strength
            5: {"stress_level": 3},                            # skip_exercise
            6: {"mood_score": 3, "stress_level": -5},          # health_check
            7: {"sleep_score": 10, "stress_level": -5},        # sleep_optimize
            8: {"stress_level": -8, "mood_score": 5},          # hobby
            9: {"sleep_score": 5, "stress_level": -2},         # rest
        }
        deltas = effects.get(action_id, {})
        state = {**prev}
        for k, v in deltas.items():
            state[k] = max(0, min(100, state.get(k, 50) + v)) if k != "weight_kg" else state.get(k, 75) + v
        state["bmi"] = round(state["weight_kg"] / (1.75 ** 2), 1)
        simulation_sessions[f"{request.session_id}_state"] = state
        simulation_sessions[f"{request.session_id}_step"] = step_num
        reward = sum(deltas.values()) * 0.3
        terminated = step_num >= 84

    gauges = gauge_calculator.calculate_all(state)
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


@app.post("/api/simulation/predict")
async def simulation_predict(session_id: str = "default") -> dict[str, Any]:
    """현재 상태에서 긍정/부정 시나리오 예측.

    같은 상태에서 '건강한 식사' vs '불건강한 식사' 등을 비교.
    """
    env = simulation_sessions.get(session_id)
    if env is None:
        return {"error": "세션을 먼저 시작해주세요. POST /api/simulation/reset"}

    current_obs = env._state.copy()
    predictions: list[dict[str, Any]] = []

    for action_def in ACTION_DEFINITIONS:
        # 임시 환경으로 시뮬레이션
        temp_env = LifeEnv()
        temp_env.reset()
        temp_env._state = current_obs.copy()
        temp_env._step_count = env._step_count

        obs, reward, _, _, _ = temp_env.step(action_def["id"])
        future_state = _obs_to_health_state(obs)
        future_gauges = gauge_calculator.calculate_all(future_state)

        predictions.append({
            "action": action_def,
            "reward": round(reward, 2),
            "predicted_state": future_state,
            "predicted_gauges": future_gauges,
        })

    # 보상 기준 정렬 (최선 → 최악)
    predictions.sort(key=lambda x: x["reward"], reverse=True)

    return {
        "session_id": session_id,
        "current_step": env._step_count,
        "predictions": predictions,
    }


# --- YOLO 식재료 인식 API ---
@app.post("/api/food/recognize")
async def food_recognize(file: UploadFile = File(...)) -> dict[str, Any]:
    """YOLO 기반 식재료 인식.

    Args:
        file: 음식/식재료 이미지.

    Returns:
        감지된 식재료 목록.
    """
    if food_recognizer is None:
        raise HTTPException(status_code=503, detail="식재료 인식 서비스가 비활성 상태입니다.")
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="허용되지 않는 파일 형식입니다.")
    image_bytes = await file.read()
    if len(image_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="파일 크기 초과 (최대 10MB)")
    detections = food_recognizer.detect(image_bytes)
    labels = food_recognizer.classify(image_bytes)

    return {
        "filename": file.filename,
        "detections": detections,
        "labels": labels,
        "count": len(detections),
    }


# --- 스케줄 기반 장기 시뮬레이션 API ---
class ScheduleSimRequest(BaseModel):
    """스케줄 시뮬레이션 요청."""
    schedule: list[dict[str, Any]]
    days: int = 30
    initial_state: dict[str, Any] | None = None


@app.post("/api/schedule/simulate")
async def schedule_simulate(request: ScheduleSimRequest) -> dict[str, Any]:
    """24시간 스케줄 기반 장기 시뮬레이션.

    Args:
        request: 스케줄 항목 리스트 + 시뮬레이션 기간.

    Returns:
        일별 상태 변화, 최종 상태, 분석 결과, 조언.
    """
    if schedule_simulator is None:
        raise HTTPException(status_code=503, detail="시뮬레이터 서비스가 초기화되지 않았습니다.")
    try:
        result = schedule_simulator.simulate(
            schedule=request.schedule,
            days=request.days,
            initial_state=request.initial_state,
        )
        return result
    except Exception as e:
        logger.exception("schedule_simulate 에러")
        raise HTTPException(status_code=500, detail="요청 처리 중 오류가 발생했습니다.")


@app.get("/api/schedule/activities")
async def get_schedule_activities() -> dict[str, Any]:
    """스케줄에 사용 가능한 활동 유형 목록."""
    activities = [
        {"key": "sleep", "label": "수면", "emoji": "😴", "color": "#748ffc", "category": "생활"},
        {"key": "meal_healthy", "label": "건강한 식사", "emoji": "🥗", "color": "#51cf66", "category": "식사"},
        {"key": "meal_normal", "label": "일반 식사", "emoji": "🍚", "color": "#ff922b", "category": "식사"},
        {"key": "meal_unhealthy", "label": "불건강한 식사", "emoji": "🍔", "color": "#ff6b6b", "category": "식사"},
        {"key": "night_snack", "label": "야식", "emoji": "🍜", "color": "#e64980", "category": "식사"},
        {"key": "exercise_cardio", "label": "유산소 운동", "emoji": "🏃", "color": "#339af0", "category": "운동"},
        {"key": "exercise_strength", "label": "근력 운동", "emoji": "🏋️", "color": "#5c7cfa", "category": "운동"},
        {"key": "work", "label": "업무/공부", "emoji": "💼", "color": "#868e96", "category": "생활"},
        {"key": "hobby", "label": "취미", "emoji": "🎸", "color": "#cc5de8", "category": "여가"},
        {"key": "rest", "label": "휴식", "emoji": "☕", "color": "#20c997", "category": "여가"},
        {"key": "commute", "label": "통근/이동", "emoji": "🚌", "color": "#adb5bd", "category": "생활"},
        {"key": "other", "label": "기타", "emoji": "📌", "color": "#ced4da", "category": "기타"},
    ]
    return {"activities": activities}


def _obs_to_health_state(obs) -> dict[str, Any]:
    """관측 벡터를 건강 상태 딕셔너리로 변환."""
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


def _build_cascade_message(
    action_def: dict[str, Any], state: dict[str, Any], reward: float
) -> dict[str, Any]:
    """행동에 따른 연쇄 효과 메시지 생성."""
    name = action_def["name"]
    domain = action_def["domain"]

    effects: list[dict[str, str]] = []

    if name == "unhealthy_meal":
        effects.append({"domain": "health", "impact": f"체중 +0.07kg → BMI {state['bmi']}"})
        effects.append({"domain": "health", "impact": "스트레스 +2 (죄책감)"})
        effects.append({"domain": "exercise", "impact": "추가 운동 필요"})
    elif name == "healthy_meal":
        effects.append({"domain": "health", "impact": "체중 미세 감소"})
        effects.append({"domain": "health", "impact": "기분 +2"})
    elif name == "skip_meal":
        effects.append({"domain": "health", "impact": "기분 -5, 스트레스 +5"})
        effects.append({"domain": "exercise", "impact": "운동 에너지 부족"})
    elif name == "cardio_exercise":
        effects.append({"domain": "health", "impact": f"수면 점수 → {state['sleep_score']}"})
        effects.append({"domain": "health", "impact": f"스트레스 → {state['stress_level']}"})
        effects.append({"domain": "food", "impact": "단백질 보충 필요"})
    elif name == "strength_exercise":
        effects.append({"domain": "health", "impact": "근력 향상"})
        effects.append({"domain": "food", "impact": "고단백 식단 권장"})
    elif name == "skip_exercise":
        effects.append({"domain": "health", "impact": "스트레스 +3"})
    elif name == "health_check":
        effects.append({"domain": "health", "impact": "불안감 감소, 기분 +3"})
    elif name == "sleep_optimize":
        effects.append({"domain": "health", "impact": f"수면 크게 개선 → {state['sleep_score']}"})
        effects.append({"domain": "exercise", "impact": "운동 효율 증가"})
    elif name == "hobby_activity":
        effects.append({"domain": "health", "impact": f"스트레스 크게 감소 → {state['stress_level']}"})
        effects.append({"domain": "food", "impact": "폭식 충동 -40%"})
        effects.append({"domain": "exercise", "impact": "운동 동기부여 증가"})

    return {
        "action_name": action_def["description"],
        "domain": domain,
        "reward": round(reward, 2),
        "severity": "positive" if reward >= 0 else ("medium" if reward > -3 else "high"),
        "effects": effects,
    }


# --- WebSocket ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket 연결 엔드포인트.

    메시지 형식:
        {"type": "echo" | "voice" | "query" | "feedback" | "subscribe", "data": ...}
    인증: query param ?token=xxx 또는 첫 메시지로 {"type":"auth","data":{"token":"xxx"}}
    """
    # 프로덕션에서는 토큰 검증
    ws_user_id = "default"
    if os.getenv("ENV") != "development":
        token = websocket.query_params.get("token", "")
        if token:
            payload = verify_token(token)
            if not payload:
                await websocket.close(code=4001, reason="Invalid token")
                return
            ws_user_id = payload.get("user_id", "default")

    await websocket.accept()
    logger.info("WebSocket 연결 수립: user=%s", ws_user_id)

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
                # 음성 텍스트 → Intent 분류 → Orchestrator → 응답
                text = data.get("text", "")
                intent = intent_classifier.classify(text)
                domain = intent_classifier.route(intent)

                try:
                    result = orchestrator.run_chain(
                        user_id=data.get("user_id", "default"),
                        domain=domain,
                        action=data,
                    )
                except Exception as e:
                    logger.error("WebSocket voice error: %s", e)
                    await websocket.send_json(
                        {"type": "error", "data": {"message": str(e)}}
                    )
                    continue

                # 텍스트 응답 생성
                response_text = _format_response(result)

                await websocket.send_json(
                    {
                        "type": "voice_result",
                        "data": {
                            "text": response_text,
                            "intent": intent,
                            "result": result,
                        },
                    }
                )

            elif msg_type == "query":
                domain = data.get("domain", "food")
                try:
                    result = orchestrator.run_chain(
                        user_id=data.get("user_id", "default"),
                        domain=domain,
                        action=data,
                    )
                    await websocket.send_json(
                        {"type": "query_result", "data": result}
                    )
                except Exception as e:
                    logger.error("WebSocket query error: %s", e)
                    await websocket.send_json(
                        {"type": "error", "data": {"message": str(e)}}
                    )

            elif msg_type == "feedback":
                user_id = data.get("user_id", "default")
                feedback_collector.collect(user_id, data)
                reward = feedback_collector.to_reward(data)
                await websocket.send_json(
                    {
                        "type": "feedback_ack",
                        "data": {"status": "received", "reward": reward},
                    }
                )

            elif msg_type == "subscribe":
                gauge_subscribers.add(websocket)
                user_id = data.get("user_id", "default")
                user_state = state_manager.to_dict(user_id)
                gauges = gauge_calculator.calculate_all(user_state)
                await websocket.send_json(
                    {"type": "gauge_update", "data": gauges}
                )

            else:
                await websocket.send_json({"error": f"unknown type: {msg_type}"})

    except WebSocketDisconnect:
        gauge_subscribers.discard(websocket)
        logger.info("WebSocket 연결 종료")


def _format_response(result: dict[str, Any]) -> str:
    """오케스트레이터 결과를 텍스트 응답으로 포맷."""
    domain = result.get("domain", "")
    agent_result = result.get("result", {})

    if domain == "food":
        recs = agent_result.get("recommendations", [])
        if recs:
            names = [r.get("name", "") for r in recs[:3]]
            return f"추천 레시피: {', '.join(names)}"
    elif domain == "exercise":
        exs = agent_result.get("exercises", [])
        if exs:
            names = [e.get("name", "") for e in exs[:3]]
            return f"추천 운동: {', '.join(names)}"
    elif domain == "health":
        summary = agent_result.get("summary", "")
        if summary:
            return summary
    elif domain == "hobby":
        hobbies = agent_result.get("hobbies", [])
        if hobbies:
            names = [h.get("name", "") for h in hobbies[:3]]
            return f"추천 취미: {', '.join(names)}"

    return "요청을 처리했습니다."
