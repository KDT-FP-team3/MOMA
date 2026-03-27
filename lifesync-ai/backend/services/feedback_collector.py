"""피드백 수집기 — 사용자 피드백을 Reward 신호로 변환."""

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class FeedbackCollector:
    """피드백 → Reward 변환기.

    사용자의 만족도 피드백을 수집하고, RL 보상 신호로 변환한다.
    """

    # 피드백 타입별 보상 매핑
    RATING_TO_REWARD: dict[int, float] = {
        1: -2.0,   # 매우 불만족
        2: -1.0,   # 불만족
        3: 0.0,    # 보통
        4: 1.5,    # 만족
        5: 3.0,    # 매우 만족
    }

    THUMBS_REWARD: dict[str, float] = {
        "up": 2.0,
        "down": -2.0,
    }

    def __init__(self) -> None:
        self._feedback_store: list[dict[str, Any]] = []

    def collect(self, user_id: str, feedback: dict[str, Any]) -> None:
        """사용자 피드백 수집.

        Args:
            user_id: 사용자 식별자.
            feedback: 피드백 데이터.
                - type: "rating" | "thumbs" | "text"
                - value: 1-5 (rating) | "up"/"down" (thumbs) | str (text)
                - domain: 피드백 대상 도메인
                - context: 추가 컨텍스트
        """
        entry = {
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "feedback": feedback,
            "reward": self.to_reward(feedback),
        }
        self._feedback_store.append(entry)
        logger.info(
            "피드백 수집: user=%s, type=%s, reward=%.1f",
            user_id,
            feedback.get("type", "unknown"),
            entry["reward"],
        )

    def to_reward(self, feedback: dict[str, Any]) -> float:
        """피드백을 보상 신호로 변환.

        Args:
            feedback: 피드백 데이터.

        Returns:
            보상 값 (-2.0 ~ 4.0).
        """
        fb_type = feedback.get("type", "")
        value = feedback.get("value")

        if fb_type == "rating" and isinstance(value, int):
            return self.RATING_TO_REWARD.get(value, 0.0)

        if fb_type == "thumbs" and isinstance(value, str):
            return self.THUMBS_REWARD.get(value, 0.0)

        if fb_type == "text":
            # 텍스트 피드백은 기본 중립 보상
            return 0.5

        return 0.0

    def get_recent(
        self, user_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """최근 피드백 조회.

        Args:
            user_id: 사용자 식별자.
            limit: 반환할 최대 건수.

        Returns:
            최근 피드백 리스트 (최신순).
        """
        user_feedbacks = [
            fb for fb in self._feedback_store if fb["user_id"] == user_id
        ]
        return user_feedbacks[-limit:][::-1]
