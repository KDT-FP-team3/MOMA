"""LifeSync AI — 플러그인 레지스트리.

팀원의 플러그인을 등록하고 관리합니다.
플러그인이 없으면 자동으로 폴백(기본 구현)을 사용합니다.

사용 예:
    from backend.core.plugin_registry import registry

    # 팀원이 자기 플러그인을 등록:
    registry.register("food_agent", MyFoodAgent())

    # 코어가 플러그인을 가져옴 (없으면 폴백):
    agent = registry.get("food_agent")
    result = agent.recommend(user_state)

미등록 슬롯:
    - fallbacks.py의 기본 구현이 자동으로 동작
    - 서비스 전체에 영향 없음
"""

from __future__ import annotations

import logging
from typing import Any

from backend.core.fallbacks import (
    BasicFoodAgent,
    BasicExerciseAgent,
    BasicHealthAgent,
    BasicHobbyAgent,
    BasicRLAgent,
    BasicImageAnalyzer,
    BasicVoiceProcessor,
    BasicKnowledgeBase,
)

logger = logging.getLogger(__name__)


class PluginRegistry:
    """플러그인 중앙 레지스트리.

    규칙:
        1. 팀원은 register()로 자기 플러그인을 등록
        2. 코어는 get()으로 플러그인을 가져옴
        3. 미등록 시 폴백이 자동으로 반환됨
        4. 플러그인 에러 시 폴백으로 자동 전환
    """

    # 슬롯별 폴백 매핑 (플러그인 미등록 시 자동 적용)
    _FALLBACKS: dict[str, type] = {
        "food_agent": BasicFoodAgent,
        "exercise_agent": BasicExerciseAgent,
        "health_agent": BasicHealthAgent,
        "hobby_agent": BasicHobbyAgent,
        "rl_agent": BasicRLAgent,
        "image_analyzer": BasicImageAnalyzer,
        "voice_processor": BasicVoiceProcessor,
        "recipe_db": BasicKnowledgeBase,
        "exercise_db": BasicKnowledgeBase,
        "health_db": BasicKnowledgeBase,
        "hobby_db": BasicKnowledgeBase,
    }

    def __init__(self):
        self._plugins: dict[str, Any] = {}
        self._fallback_instances: dict[str, Any] = {}

    def register(self, slot: str, plugin: Any) -> None:
        """플러그인 등록.

        Args:
            slot: 플러그인 슬롯 이름 (예: "food_agent", "rl_agent")
            plugin: 해당 인터페이스를 구현한 객체

        Raises:
            ValueError: 알 수 없는 슬롯 이름
        """
        if slot not in self._FALLBACKS:
            valid = ", ".join(sorted(self._FALLBACKS.keys()))
            raise ValueError(
                f"알 수 없는 플러그인 슬롯: '{slot}'. 유효한 슬롯: {valid}"
            )
        # 에이전트 슬롯은 recommend/analyze_checkup 메서드 필수
        agent_slots = {"food_agent", "exercise_agent", "health_agent", "hobby_agent"}
        if slot in agent_slots:
            has_recommend = hasattr(plugin, "recommend")
            has_checkup = hasattr(plugin, "analyze_checkup")
            if not has_recommend and not has_checkup:
                logger.warning(
                    "플러그인 %s에 recommend()/analyze_checkup() 메서드가 없습니다: %s",
                    slot, type(plugin).__name__,
                )
        self._plugins[slot] = plugin
        logger.info("플러그인 등록: %s → %s", slot, type(plugin).__name__)

    def get(self, slot: str) -> Any:
        """플러그인 가져오기 (없으면 폴백).

        Args:
            slot: 플러그인 슬롯 이름

        Returns:
            등록된 플러그인 또는 폴백 인스턴스
        """
        # 1. 등록된 플러그인이 있으면 사용
        if slot in self._plugins:
            return self._plugins[slot]

        # 2. 폴백 인스턴스 캐시 확인
        if slot in self._fallback_instances:
            return self._fallback_instances[slot]

        # 3. 폴백 인스턴스 생성 + 캐시
        fallback_cls = self._FALLBACKS.get(slot)
        if fallback_cls is None:
            raise ValueError(f"알 수 없는 플러그인 슬롯: '{slot}'")

        instance = fallback_cls()
        self._fallback_instances[slot] = instance
        logger.info("폴백 사용: %s → %s", slot, type(instance).__name__)
        return instance

    def is_plugin_active(self, slot: str) -> bool:
        """해당 슬롯에 팀원 플러그인이 등록되었는지 확인."""
        return slot in self._plugins

    def status(self) -> dict[str, dict[str, str]]:
        """전체 플러그인 상태 조회.

        Returns:
            {slot: {"status": "plugin"|"fallback", "class": 클래스명}}
        """
        result = {}
        for slot in self._FALLBACKS:
            if slot in self._plugins:
                result[slot] = {
                    "status": "plugin",
                    "class": type(self._plugins[slot]).__name__,
                }
            else:
                result[slot] = {
                    "status": "fallback",
                    "class": self._FALLBACKS[slot].__name__,
                }
        return result

    def list_slots(self) -> list[str]:
        """사용 가능한 모든 플러그인 슬롯 목록."""
        return sorted(self._FALLBACKS.keys())


# ── 전역 싱글톤 레지스트리 ────────────────────────────────
# 앱 전체에서 하나의 레지스트리를 공유합니다.
registry = PluginRegistry()
