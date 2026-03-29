"""플러그인 상태 서포트 에이전트.

각 플러그인의 active/fallback 상태, 오케스트레이터 연동, CASCADE 활용도를 점검합니다.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def check_plugin_status() -> dict[str, Any]:
    """플러그인 레지스트리에서 각 슬롯의 활성 상태를 확인합니다."""
    try:
        from backend.core.plugin_registry import registry
        status = registry.status()
    except Exception as e:
        logger.warning("[PluginHealth] 레지스트리 접근 실패: %s", e)
        return {"slots": {}, "error": str(e)}

    active = 0
    fallback = 0
    details = {}

    for slot, info in status.items():
        is_active = info.get("status") == "plugin"
        details[slot] = {
            "status": "active" if is_active else "fallback",
            "class": info.get("class", "unknown"),
        }
        if is_active:
            active += 1
        else:
            fallback += 1

    return {
        "slots": details,
        "active_count": active,
        "fallback_count": fallback,
        "total": active + fallback,
    }


def check_cascade_coverage() -> dict[str, Any]:
    """CASCADE_RULES에서 각 도메인의 연결 상태를 분석합니다."""
    try:
        from backend.agents.orchestrator import CASCADE_RULES
    except ImportError:
        return {"coverage": {}, "error": "orchestrator import 실패"}

    coverage = {}
    for source, targets in CASCADE_RULES.items():
        coverage[source] = {
            "targets": list(targets.keys()),
            "count": len(targets),
        }

    total_rules = sum(c["count"] for c in coverage.values())
    return {
        "coverage": coverage,
        "total_rules": total_rules,
        "domains_with_cascade": len(coverage),
    }


def run() -> dict[str, Any]:
    """플러그인 상태 점검 실행."""
    logger.info("[PluginHealth] 점검 시작")
    status = check_plugin_status()
    cascade = check_cascade_coverage()

    score = 100
    if status.get("fallback_count", 0) > 0:
        score -= status["fallback_count"] * 10

    return {
        "agent": "plugin_health",
        "plugin_status": status,
        "cascade": cascade,
        "summary": {
            "active": status.get("active_count", 0),
            "fallback": status.get("fallback_count", 0),
            "cascade_rules": cascade.get("total_rules", 0),
            "score": max(0, score),
        },
    }
