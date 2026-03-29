"""API 헬스 서포트 에이전트.

주요 API 엔드포인트의 응답 가능 여부를 점검합니다.
외부 HTTP 호출 없이, 라우터 등록 상태와 서비스 가용성을 내부적으로 확인합니다.
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# 점검 대상 핵심 엔드포인트
_CRITICAL_ENDPOINTS = [
    {"path": "/health", "method": "GET", "category": "system"},
    {"path": "/api/plugins/status", "method": "GET", "category": "system"},
    {"path": "/api/admin/status", "method": "GET", "category": "admin"},
    {"path": "/api/dashboard/{uid}", "method": "GET", "category": "user"},
    {"path": "/api/query", "method": "POST", "category": "user"},
    {"path": "/api/simulation/reset", "method": "POST", "category": "ai"},
    {"path": "/api/photo/upload", "method": "POST", "category": "ai"},
    {"path": "/api/admin/team-progress", "method": "GET", "category": "admin"},
]


def check_services() -> dict[str, Any]:
    """백엔드 서비스(gauge_calculator, retrain_scheduler 등) 가용성을 확인합니다."""
    services = {}

    try:
        from backend.app.services_init import gauge_calculator, retrain_scheduler, ppo_agent
        services["gauge_calculator"] = gauge_calculator is not None
        services["retrain_scheduler"] = retrain_scheduler is not None
        services["ppo_agent"] = ppo_agent is not None
    except Exception as e:
        logger.warning("[APIHealth] 서비스 초기화 확인 실패: %s", e)
        services["error"] = str(e)

    return services


def check_env_keys() -> dict[str, Any]:
    """필수 환경변수 설정 여부를 확인합니다."""
    keys = {
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY", "")),
        "DATABASE_URL": bool(os.getenv("DATABASE_URL", "")),
        "JWT_SECRET": bool(os.getenv("JWT_SECRET", "")),
    }
    configured = sum(keys.values())
    return {"keys": keys, "configured": configured, "total": len(keys)}


def check_router_registration() -> dict[str, Any]:
    """3개 라우터 등록 상태를 확인합니다."""
    routers = {}
    try:
        from backend.app.routers import ai_router, api_router, admin_router
        routers["ai_router"] = hasattr(ai_router, "router")
        routers["api_router"] = hasattr(api_router, "router")
        routers["admin_router"] = hasattr(admin_router, "router")
    except ImportError as e:
        routers["error"] = str(e)

    return routers


def run() -> dict[str, Any]:
    """API 헬스 점검 실행."""
    logger.info("[APIHealth] 점검 시작")
    services = check_services()
    env = check_env_keys()
    routers = check_router_registration()

    score = 100
    if not services.get("gauge_calculator"):
        score -= 15
    if env["configured"] < env["total"]:
        score -= (env["total"] - env["configured"]) * 10
    if "error" in routers:
        score -= 30

    return {
        "agent": "api_health",
        "services": services,
        "env_keys": env,
        "routers": routers,
        "endpoints": _CRITICAL_ENDPOINTS,
        "summary": {
            "services_ok": sum(1 for v in services.values() if v is True),
            "env_configured": env["configured"],
            "routers_ok": sum(1 for v in routers.values() if v is True),
            "score": max(0, score),
        },
    }
