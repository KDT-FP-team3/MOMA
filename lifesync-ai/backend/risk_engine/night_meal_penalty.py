"""야식 패널티 계산기 — 시간대별 식사 패널티 산출.

예시: 야식 라면 (23시) → -5 → 수면 -35% → 운동 -20% → 체중 목표 +2일 지연
"""

from typing import Any


# 음식 타입별 가중치 (야식 시 더 나쁜 음식)
FOOD_TYPE_MULTIPLIER: dict[str, float] = {
    "라면": 1.5,
    "치킨": 1.4,
    "피자": 1.3,
    "떡볶이": 1.2,
    "삼겹살": 1.3,
    "짜장면": 1.2,
    "짬뽕": 1.2,
    "과자": 1.1,
    "아이스크림": 1.1,
    "삶은달걀": 0.3,
    "샐러드": 0.2,
    "요거트": 0.3,
    "과일": 0.4,
    "물": 0.0,
}


class NightMealPenalty:
    """야식 패널티 계산기.

    예시: 야식 라면 (23시) → -5 → 수면 -35% → 운동 -20% → 체중 목표 +2일 지연
    """

    def calculate(self, meal: dict[str, Any], hour: int) -> float:
        """시간대와 식사 정보 기반 패널티 계산.

        Args:
            meal: 식사 정보 (name, calories, food_type 등).
            hour: 식사 시각 (0-23).

        Returns:
            패널티 값 (음수, 야식이 아니면 0.0).
        """
        if hour < 21:
            return 0.0

        # 시간대별 기본 패널티
        if hour == 21:
            base_penalty = -2.0
        elif hour == 22:
            base_penalty = -3.0
        elif hour == 23:
            base_penalty = -5.0
        else:  # 0시~4시
            base_penalty = -7.0

        # 음식 타입별 가중치
        food_name = meal.get("name", "")
        multiplier = 1.0
        for food_type, mult in FOOD_TYPE_MULTIPLIER.items():
            if food_type in food_name:
                multiplier = mult
                break

        # 칼로리 기반 추가 패널티
        calories = meal.get("calories", 0)
        calorie_penalty = 0.0
        if calories > 500:
            calorie_penalty = -1.0
        elif calories > 300:
            calorie_penalty = -0.5

        return (base_penalty * multiplier) + calorie_penalty

    def estimate_cascade_effect(self, penalty: float) -> dict[str, float]:
        """패널티의 연쇄 효과 추정 (수면, 운동, 체중 등).

        Args:
            penalty: 야식 패널티 값 (음수).

        Returns:
            연쇄 효과 딕셔너리.
        """
        abs_penalty = abs(penalty)

        return {
            "sleep_quality_delta": penalty * 7.0,        # 수면 질 % 변화
            "next_day_exercise_delta": penalty * 4.0,    # 다음날 운동 성과 % 변화
            "weight_goal_delay_days": abs_penalty * 0.4,  # 체중 목표 지연 일수
            "calorie_surplus": abs_penalty * 50,          # 잉여 칼로리 추정
            "stress_increase": abs_penalty * 2.0,         # 스트레스 증가분
        }
