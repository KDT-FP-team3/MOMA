"""LifeSync AI — FastAPI 진입점.

이 파일은 앱 설정, 미들웨어, 라우터 등록만 담당한다.
실제 엔드포인트 로직은 routers/ 패키지에 분리되어 있다.

구조:
  main.py                (이 파일 — 공통)
  routers/ai_router.py   (그룹 A — AI/ML 엔드포인트)
  routers/api_router.py  (그룹 B — 백엔드 API 엔드포인트)

각 그룹은 자기 router 파일만 수정하면 되므로 git 충돌이 발생하지 않는다.
"""

from dotenv import load_dotenv
load_dotenv(encoding="utf-8")

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.services.kakao_auth import verify_token

logger = logging.getLogger(__name__)


# ============================================================
# 앱 생명주기 (시작/종료)
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 이벤트."""
    logger.info("LifeSync AI 서버 시작")
    yield
    # api_router의 state_manager가 있으면 정리
    try:
        from backend.app.routers.api_router import state_manager
        if state_manager is not None:
            state_manager.close()
    except Exception:
        pass
    logger.info("LifeSync AI 서버 종료")


app = FastAPI(title="LifeSync AI", version="0.3.0", lifespan=lifespan)


# ============================================================
# 미들웨어 1: 보안 헤더
# ============================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """보안 응답 헤더 자동 추가 (XSS, Clickjacking, HSTS 방어)."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if os.getenv("ENV") == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


app.add_middleware(SecurityHeadersMiddleware)


# ============================================================
# 미들웨어 2: CORS
# ============================================================

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


# ============================================================
# 미들웨어 3: JWT 인증
# ============================================================

# 인증 없이 접근 가능한 경로
PUBLIC_PATHS = {
    "/health", "/docs", "/openapi.json", "/redoc",
    "/api/auth/kakao/login-url", "/api/auth/kakao/callback",
    "/api/onboarding", "/api/plugins/status", "/api/admin/status", "/api/device/info",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """JWT 토큰 검증.

    - PUBLIC_PATHS, OPTIONS, WebSocket: 인증 생략
    - ENV=development: 인증 생략 (로컬 개발용)
    - 그 외: Authorization: Bearer <token> 필수
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 공개 경로 / CORS preflight / WebSocket → 통과
        if path in PUBLIC_PATHS or request.method == "OPTIONS" or path.startswith("/ws"):
            return await call_next(request)

        # 개발 환경 → 인증 생략 (명시적으로 "development"만 허용)
        if os.getenv("ENV", "production") == "development":
            return await call_next(request)

        # Bearer 토큰 검증
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

        if not token:
            from starlette.responses import JSONResponse
            client_ip = request.client.host if request.client else "?"
            logger.warning("인증 실패: 토큰 없음 (IP=%s, path=%s)", client_ip, path)
            return JSONResponse(status_code=401, content={"detail": "인증 토큰이 필요합니다."})

        payload = verify_token(token)
        if not payload:
            from starlette.responses import JSONResponse
            client_ip = request.client.host if request.client else "?"
            logger.warning("인증 실패: 유효하지 않은 토큰 (IP=%s, path=%s)", client_ip, path)
            return JSONResponse(status_code=401, content={"detail": "유효하지 않은 토큰입니다."})

        request.state.user = payload
        return await call_next(request)


app.add_middleware(AuthMiddleware)


# ============================================================
# 미들웨어 4: Rate Limiting (IP 기반, 분당 60회)
# ============================================================

import time
from collections import defaultdict

_rate_limit_store: dict[str, list[float]] = defaultdict(list)
_rate_limit_last_cleanup = 0.0  # 마지막 정리 시각
RATE_LIMIT_MAX = 60
RATE_LIMIT_WINDOW = 60  # 초
_CLEANUP_INTERVAL = 300  # 5분마다 오래된 IP 정리


class RateLimitMiddleware(BaseHTTPMiddleware):
    """IP 기반 Rate Limiting + 주기적 메모리 정리."""

    async def dispatch(self, request: Request, call_next):
        global _rate_limit_last_cleanup
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # 5분마다 전체 정리 (오래된 IP 제거 → 메모리 누수 방지)
        if now - _rate_limit_last_cleanup > _CLEANUP_INTERVAL:
            stale = [ip for ip, ts in _rate_limit_store.items()
                     if not ts or now - ts[-1] > RATE_LIMIT_WINDOW]
            for ip in stale:
                del _rate_limit_store[ip]
            _rate_limit_last_cleanup = now

        # 윈도우 밖 기록 제거
        _rate_limit_store[client_ip] = [
            t for t in _rate_limit_store[client_ip] if now - t < RATE_LIMIT_WINDOW
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


# ============================================================
# 헬스체크 (공통)
# ============================================================

@app.get("/health")
async def health_check() -> dict[str, str]:
    """헬스체크 — Railway/Docker healthcheck용."""
    return {"status": "ok"}


@app.get("/api/plugins/status")
async def plugin_status():
    """플러그인 상태 조회 — 각 슬롯의 활성/폴백 상태 확인."""
    from backend.core.plugin_registry import registry
    return {"plugins": registry.status()}


@app.get("/api/device/info")
async def device_info():
    """GPU/CPU 디바이스 정보."""
    from backend.core.device import get_device_info
    return get_device_info()


@app.get("/api/admin/status")
async def admin_status():
    """관리자 통합 상태 — 모든 시스템 정보를 한 번에 조회.

    플러그인, GPU, API 키, 서비스 상태를 단일 응답으로 반환.
    """
    from backend.core.plugin_registry import registry
    from backend.core.device import get_device_info

    # API 키 상태 (값은 노출하지 않고 설정 여부만)
    env_keys = {
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY", "")),
        "DATABASE_URL": bool(os.getenv("DATABASE_URL", "")),
        "KMA_API_KEY": bool(os.getenv("KMA_API_KEY", "")),
        "AIRKOREA_API_KEY": bool(os.getenv("AIRKOREA_API_KEY", "")),
        "JWT_SECRET": bool(os.getenv("JWT_SECRET", "")),
        "KAKAO_CLIENT_ID": bool(os.getenv("KAKAO_CLIENT_ID", "")),
        "KAKAO_CLIENT_SECRET": bool(os.getenv("KAKAO_CLIENT_SECRET", "")),
    }
    keys_ok = sum(env_keys.values())
    keys_total = len(env_keys)

    # 서비스 상태
    from backend.app.services_init import gauge_calculator, retrain_scheduler, ppo_agent
    services = {
        "gauge_calculator": gauge_calculator is not None,
        "retrain_scheduler": retrain_scheduler is not None,
        "ppo_agent": ppo_agent is not None,
    }

    return {
        "server": {"status": "running", "version": app.version, "env": os.getenv("ENV", "development")},
        "api_keys": {"configured": keys_ok, "total": keys_total, "details": env_keys},
        "plugins": registry.status(),
        "device": get_device_info(),
        "services": services,
    }


# ============================================================
# 플러그인 자동 등록 (팀원 플러그인 탐색)
# ============================================================

from backend.plugins import auto_register_plugins
auto_register_plugins()


# ============================================================
# 라우터 등록
#
# 그룹 A → ai_router   (사진분석, 시뮬레이션, 모델동기화, RL)
# 그룹 B → api_router   (쿼리, 인증, 대시보드, 피드백, WebSocket)
#
# 각 그룹은 자기 router 파일만 수정하면 충돌 없음.
# ============================================================

from backend.app.routers.ai_router import router as ai_router
from backend.app.routers.api_router import router as api_router

app.include_router(ai_router)
app.include_router(api_router)
