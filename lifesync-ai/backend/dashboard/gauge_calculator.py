"""6개 계기판 지수 계산기 — 대시보드 표시용 종합 지수 산출.

6개 게이지: 활성산소(ROS), 혈액청정도, 탈모위험도, 수면점수, 스트레스수준, 주간목표달성률
"""

from typing import Any


class GaugeCalculator:
    """6개 계기판 지수 계산기."""

    GAUGE_NAMES: list[str] = [
        "reactive_oxygen",
        "blood_purity",
        "hair_loss_risk",
        "sleep_score",
        "stress_level",
        "weekly_achievement",
    ]

    def calculate_all(self, user_state: dict[str, Any]) -> dict[str, float]:
        """모든 계기판 지수 계산.

        Args:
            user_state: 사용자 상태 벡터 딕셔너리.

        Returns:
            6개 게이지별 0-100 점수.
        """
        return {
            name: self.calculate_single(name, user_state)
            for name in self.GAUGE_NAMES
        }

    def calculate_single(
        self, gauge_name: str, user_state: dict[str, Any]
    ) -> float:
        """단일 계기판 지수 계산.

        Args:
            gauge_name: 게이지 이름.
            user_state: 사용자 상태 벡터 딕셔너리.

        Returns:
            0-100 범위의 게이지 점수.
        """
        calculators = {
            "reactive_oxygen": self._calc_reactive_oxygen,
            "blood_purity": self._calc_blood_purity,
            "hair_loss_risk": self._calc_hair_loss_risk,
            "sleep_score": self._calc_sleep_score,
            "stress_level": self._calc_stress_level,
            "weekly_achievement": self._calc_weekly_achievement,
        }

        calc_fn = calculators.get(gauge_name)
        if calc_fn is None:
            return 0.0
        return max(0.0, min(100.0, calc_fn(user_state)))

    def _calc_reactive_oxygen(self, state: dict[str, Any]) -> float:
        """활성산소(ROS) 지수 계산.

        악화: 과격한 운동, 튀김/가공식품, 흡연/음주, 스트레스
        개선: 항산화 식품, 적정 운동, 충분한 수면
        """
        base = 65.0
        stress = state.get("stress_level", 50.0)
        sleep = state.get("sleep_score", 50.0)
        calorie_intake = state.get("calorie_intake", 2000.0)

        # 스트레스가 높으면 ROS 증가 (점수 하락)
        stress_effect = (stress - 50) * -0.3
        # 수면이 좋으면 ROS 감소 (점수 증가)
        sleep_effect = (sleep - 50) * 0.2
        # 과식 시 ROS 증가
        calorie_effect = max(0, (calorie_intake - 2500)) * -0.01

        return base + stress_effect + sleep_effect + calorie_effect

    def _calc_blood_purity(self, state: dict[str, Any]) -> float:
        """혈액 청정도 계산.

        악화: 고지방 식이, 운동 부족, 야식 습관, 수분 부족
        개선: 유산소 운동 30분 이상, 수분 2L 이상, 채소 섭취
        """
        base = 70.0
        calorie_burned = state.get("calorie_burned", 0.0)
        bmi = state.get("bmi", 22.0)

        # 운동량에 따른 개선
        exercise_effect = min(calorie_burned / 300 * 10, 15.0)
        # BMI가 정상 범위를 벗어나면 하락
        bmi_effect = -abs(bmi - 22.0) * 2.0

        return base + exercise_effect + bmi_effect

    def _calc_hair_loss_risk(self, state: dict[str, Any]) -> float:
        """탈모 위험도 계산 (낮을수록 좋음, 0-100%).

        악화: 스트레스, 수면 부족, 영양 불균형, 두피 자극
        개선: 균형 식단, 스트레스 관리, 두피 마사지
        """
        base = 20.0
        stress = state.get("stress_level", 50.0)
        sleep = state.get("sleep_score", 50.0)

        # 스트레스가 높으면 탈모 위험 증가
        stress_effect = max(0, (stress - 50)) * 0.3
        # 수면 부족 시 탈모 위험 증가
        sleep_effect = max(0, (50 - sleep)) * 0.2

        return base + stress_effect + sleep_effect

    def _calc_sleep_score(self, state: dict[str, Any]) -> float:
        """수면 점수 계산.

        StateVector에 이미 sleep_score가 있으면 직접 사용.
        """
        return state.get("sleep_score", 50.0)

    def _calc_stress_level(self, state: dict[str, Any]) -> float:
        """스트레스 수준 계산.

        StateVector에 이미 stress_level이 있으면 직접 사용.
        """
        return state.get("stress_level", 50.0)

    def _calc_weekly_achievement(self, state: dict[str, Any]) -> float:
        """주간 목표 달성률 계산 (0-100%).

        weekly_achievement 필드는 0~1 범위이므로 100을 곱한다.
        """
        achievement = state.get("weekly_achievement", 0.0)
        if achievement <= 1.0:
            return achievement * 100.0
        return achievement
