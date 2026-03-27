"""다축 연쇄 보상 함수.

R(s,a,t) = w1*r_taste + w2*r_health + w3*r_fitness + w4*r_mood + w5*r_habit
           - penalty_night - penalty_risk - penalty_skip + bonus_photo_goal
"""

from datetime import datetime
from typing import Any

import numpy as np

# --- 패널티 상수 ---
PENALTY_NIGHT_MEAL: float = -5.0  # 22시 이후 식사
PENALTY_FRIED: float = -4.0  # 튀김류
PENALTY_OUTDOOR_DUST: float = -4.0  # 미세먼지 76 이상 야외 운동

# --- 보너스 상수 ---
BONUS_AIRFRYER: float = 2.0  # 에어프라이어 수용
BONUS_HOBBY_30MIN: float = 2.0  # 취미 30분 이상
BONUS_HEALTH_CHECK: float = 4.0  # 건강검진 이행
BONUS_PHOTO_50PCT: float = 3.0  # 사진 목표 50% 달성

# --- 기본 가중치 ---
DEFAULT_WEIGHTS: dict[str, float] = {
    "taste": 1.0,
    "health": 1.5,
    "fitness": 1.2,
    "mood": 1.0,
    "habit": 1.3,
}


class CrossDomainReward:
    """크로스 도메인 보상 계산기.

    R(s,a,t) = w1*r_taste + w2*r_health + w3*r_fitness + w4*r_mood + w5*r_habit
               - penalty_night - penalty_risk - penalty_skip + bonus_photo_goal
    """

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or DEFAULT_WEIGHTS.copy()

    def compute(
        self,
        state: dict[str, Any],
        action: dict[str, Any],
        timestamp: float,
    ) -> float:
        """전체 보상 값 계산.

        Args:
            state: 현재 사용자 상태 벡터 (dict 형태).
            action: 수행한 행동 정보.
            timestamp: 행동 시각 (Unix timestamp).

        Returns:
            최종 보상 값 (float).
        """
        # --- 개별 보상 축 ---
        r_taste = state.get("taste_score", 0.0)
        r_health = state.get("health_score", 0.0)
        r_fitness = state.get("fitness_score", 0.0)
        r_mood = state.get("mood_score", 0.0)
        r_habit = state.get("habit_score", 0.0)

        # --- 가중합 ---
        weighted_sum = (
            self.weights["taste"] * r_taste
            + self.weights["health"] * r_health
            + self.weights["fitness"] * r_fitness
            + self.weights["mood"] * r_mood
            + self.weights["habit"] * r_habit
        )

        # --- 패널티 & 보너스 ---
        penalty = self.compute_penalty(state, action, timestamp)
        bonus = self.compute_bonus(state, action)

        return float(weighted_sum + penalty + bonus)

    def compute_penalty(
        self,
        state: dict[str, Any],
        action: dict[str, Any],
        timestamp: float | None = None,
    ) -> float:
        """패널티 계산 (야식, 튀김, 미세먼지).

        Args:
            state: 현재 사용자 상태.
            action: 수행한 행동 정보.
            timestamp: 행동 시각 (Unix timestamp). None이면 시간 패널티 무시.

        Returns:
            패널티 합계 (음수 값).
        """
        penalty = 0.0

        # 야식 패널티: 22시 이후 식사
        if timestamp is not None:
            hour = datetime.fromtimestamp(timestamp).hour
            if hour >= 22 and action.get("type") == "meal":
                penalty += PENALTY_NIGHT_MEAL

        # 튀김류 패널티
        cooking_method = action.get("cooking_method", "")
        if cooking_method in ("fried", "deep_fried", "튀김"):
            penalty += PENALTY_FRIED

        # 미세먼지 야외 운동 패널티
        dust_level = state.get("pm10", 0.0)
        is_outdoor = action.get("is_outdoor", False)
        if dust_level >= 76 and is_outdoor:
            penalty += PENALTY_OUTDOOR_DUST

        # 스킵 패널티 (계획된 활동 미이행)
        if action.get("skipped", False):
            penalty += -2.0

        return penalty

    def compute_bonus(
        self, state: dict[str, Any], action: dict[str, Any]
    ) -> float:
        """보너스 계산 (에어프라이어, 취미, 건강검진, 사진 목표).

        Args:
            state: 현재 사용자 상태.
            action: 수행한 행동 정보.

        Returns:
            보너스 합계 (양수 값).
        """
        bonus = 0.0

        # 에어프라이어 사용 보너스
        if action.get("cooking_method") == "airfryer":
            bonus += BONUS_AIRFRYER

        # 취미 30분 이상 보너스
        hobby_duration = action.get("hobby_duration_min", 0)
        if hobby_duration >= 30:
            bonus += BONUS_HOBBY_30MIN

        # 건강검진 이행 보너스
        if action.get("health_check_done", False):
            bonus += BONUS_HEALTH_CHECK

        # 사진 목표 50% 이상 달성 보너스
        photo_progress = state.get("photo_goal_progress", 0.0)
        if photo_progress >= 0.5:
            bonus += BONUS_PHOTO_50PCT

        return bonus
