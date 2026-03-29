"""공유 서비스 초기화 — 라우터 간 중복 초기화 방지.

GaugeCalculator, RetrainScheduler, PPOAgent 등
ai_router와 api_router 양쪽에서 사용하는 서비스를 한 번만 초기화합니다.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _safe_init(name: str, factory) -> Any:
    """서비스 안전 초기화. 실패 시 None 반환 + 로그."""
    try:
        instance = factory()
        logger.info("서비스 초기화 성공: %s", name)
        return instance
    except Exception:
        logger.exception("서비스 초기화 실패 (비활성): %s", name)
        return None


# ── 공유 서비스 (한 번만 초기화) ──────────────────────────

from backend.dashboard.gauge_calculator import GaugeCalculator
from backend.rl_engine.retrain_scheduler import RetrainScheduler
from backend.rl_engine.ppo_agent import PPOAgent

gauge_calculator = _safe_init("GaugeCalculator", GaugeCalculator)
retrain_scheduler = _safe_init("RetrainScheduler", RetrainScheduler)
ppo_agent = _safe_init("PPOAgent", PPOAgent)
