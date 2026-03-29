"""코어 모니터링 에이전트.

4개 서포트 에이전트를 실행하고 결과를 종합하여
CLAUDE.md에 반영하고 API로 조회 가능한 상태를 관리합니다.
"""

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any

from backend.agents.monitoring import (
    code_quality_check,
    plugin_health_check,
    api_health_check,
    security_check,
    claude_md_updater,
)

logger = logging.getLogger(__name__)

# 최근 점검 결과 (API 조회용)
_latest_result: dict[str, Any] = {}
_lock = threading.Lock()


def run_all_checks() -> dict[str, Any]:
    """모든 서포트 에이전트를 실행하고 결과를 종합합니다."""
    global _latest_result
    logger.info("[CoreAgent] === 전체 점검 시작 ===")
    start = time.time()

    results = {}

    # 서포트 에이전트 순차 실행 (각각 독립적이므로 한 번에 실행)
    agents = [
        ("code_quality", code_quality_check),
        ("plugin_health", plugin_health_check),
        ("api_health", api_health_check),
        ("security", security_check),
    ]

    for name, agent in agents:
        try:
            results[name] = agent.run()
        except Exception as e:
            logger.exception("[CoreAgent] %s 에이전트 실패", name)
            results[name] = {"agent": name, "summary": {"score": 0, "error": str(e)}}

    # 종합 점수 계산
    scores = [r.get("summary", {}).get("score", 0) for r in results.values()]
    overall = round(sum(scores) / len(scores)) if scores else 0

    results["overall"] = {
        "score": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_sec": round(time.time() - start, 2),
        "agents_run": len(agents),
    }

    # CLAUDE.md 업데이트
    try:
        update_result = claude_md_updater.update_all(results)
        results["claude_md_update"] = update_result
        logger.info("[CoreAgent] CLAUDE.md 업데이트: %s", update_result)
    except Exception as e:
        logger.exception("[CoreAgent] CLAUDE.md 업데이트 실패")
        results["claude_md_update"] = {"error": str(e)}

    # 결과 저장
    with _lock:
        _latest_result = results

    logger.info("[CoreAgent] === 전체 점검 완료 (%.1f초, 점수 %d/100) ===",
                time.time() - start, overall)
    return results


def get_latest_result() -> dict[str, Any]:
    """최근 점검 결과를 반환합니다."""
    with _lock:
        return _latest_result.copy()


class MonitoringScheduler:
    """주기적으로 코어 에이전트를 실행하는 스케줄러.

    retrain_scheduler.py와 동일한 패턴을 사용합니다.
    """

    def __init__(self, interval_hours: float = 6.0):
        self._interval = interval_hours * 3600
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """백그라운드 스레드에서 주기적 점검을 시작합니다."""
        if self._thread and self._thread.is_alive():
            logger.warning("[MonitoringScheduler] 이미 실행 중")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="monitoring-agent")
        self._thread.start()
        logger.info("[MonitoringScheduler] 시작 (주기: %.1f시간)", self._interval / 3600)

    def stop(self) -> None:
        """스케줄러를 중지합니다."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("[MonitoringScheduler] 중지")

    def _loop(self) -> None:
        """주기적 실행 루프."""
        # 시작 후 30초 대기 (서버 초기화 완료 대기)
        self._stop_event.wait(30)

        while not self._stop_event.is_set():
            try:
                run_all_checks()
            except Exception:
                logger.exception("[MonitoringScheduler] 점검 실행 실패")

            self._stop_event.wait(self._interval)
