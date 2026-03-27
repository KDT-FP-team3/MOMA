"""입력 데이터 검증 시스템 — 범위 검사, 이상치 탐지, 신뢰도 점수 산출."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# 필드별 유효 범위 정의 (min, max)
FIELD_RANGES: dict[str, tuple[float, float]] = {
    "weight_kg": (20.0, 300.0),
    "height_cm": (100.0, 250.0),
    "sleep_hours": (0.0, 24.0),
    "calorie_intake": (0.0, 10000.0),
    "stress_level": (0.0, 100.0),
    "mood_score": (0.0, 100.0),
    "bmi": (10.0, 60.0),
}

# 급격한 변화 감지 임계값 (주당 최대 허용 변화량)
WEEKLY_CHANGE_LIMITS: dict[str, float] = {
    "weight_kg": 5.0,
}

# 불가능한 조합 규칙
IMPOSSIBLE_COMBINATIONS: list[dict[str, Any]] = [
    {
        "description": "BMI does not match weight and height",
        "fields": ["weight_kg", "height_cm", "bmi"],
    },
    {
        "description": "Sleep hours exceed 24 when combined with exercise",
        "fields": ["sleep_hours", "exercise_hours"],
    },
]


class InputValidator:
    """사용자 입력 데이터의 유효성을 검증하고 신뢰도 점수를 산출한다.

    범위 검사, 음수 값 탐지, 급격한 변화 감지, 불가능한 조합 검출을
    통해 데이터 품질을 평가한다.

    Attributes:
        _previous_data: 이전 입력 데이터 (이상치 변화 감지용).
    """

    def __init__(self) -> None:
        self._previous_data: dict[str, float] = {}

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """입력 데이터를 검증하고 신뢰도 점수를 반환한다.

        Args:
            data: 검증할 사용자 입력 데이터. 키는 필드명, 값은 숫자.

        Returns:
            검증 결과 딕셔너리:
                - valid (bool): 모든 검증 통과 여부.
                - confidence_score (float): 0.0(확실히 잘못됨) ~ 1.0(완벽히 정상).
                - warnings (list[str]): 경고 메시지 목록.
        """
        warnings: list[str] = []
        penalties: list[float] = []

        # 1. 음수 값 검사
        negative_penalties = self._check_negative_values(data)
        for field, penalty in negative_penalties:
            warnings.append(f"Negative value detected for '{field}': {data[field]}")
            penalties.append(penalty)

        # 2. 범위 검사
        range_penalties = self._check_ranges(data)
        for field, value, min_val, max_val, penalty in range_penalties:
            warnings.append(
                f"'{field}' value {value} is out of range [{min_val}, {max_val}]"
            )
            penalties.append(penalty)

        # 3. 급격한 변화 감지
        change_penalties = self._check_sudden_changes(data)
        for field, prev, curr, limit, penalty in change_penalties:
            warnings.append(
                f"Sudden change in '{field}': {prev} -> {curr} "
                f"(exceeds weekly limit of {limit})"
            )
            penalties.append(penalty)

        # 4. 불가능한 조합 감지
        combo_penalties = self._check_impossible_combinations(data)
        for description, penalty in combo_penalties:
            warnings.append(f"Impossible combination: {description}")
            penalties.append(penalty)

        # 신뢰도 점수 계산
        confidence_score = self._calculate_confidence(penalties)

        # 이전 데이터 업데이트
        for key, value in data.items():
            if isinstance(value, (int, float)):
                self._previous_data[key] = float(value)

        valid = len(warnings) == 0

        if warnings:
            logger.warning(
                "입력 검증 경고 %d건, 신뢰도=%.2f", len(warnings), confidence_score
            )

        return {
            "valid": valid,
            "confidence_score": confidence_score,
            "warnings": warnings,
        }

    def _check_negative_values(
        self, data: dict[str, Any]
    ) -> list[tuple[str, float]]:
        """음수 값을 검사한다.

        Args:
            data: 검증할 데이터.

        Returns:
            (필드명, 패널티) 튜플 리스트.
        """
        results: list[tuple[str, float]] = []
        for field, value in data.items():
            if isinstance(value, (int, float)) and value < 0:
                results.append((field, 0.5))
        return results

    def _check_ranges(
        self, data: dict[str, Any]
    ) -> list[tuple[str, float, float, float, float]]:
        """필드별 유효 범위를 검사한다.

        Args:
            data: 검증할 데이터.

        Returns:
            (필드명, 값, 최소값, 최대값, 패널티) 튜플 리스트.
        """
        results: list[tuple[str, float, float, float, float]] = []
        for field, (min_val, max_val) in FIELD_RANGES.items():
            if field not in data:
                continue
            value = data[field]
            if not isinstance(value, (int, float)):
                continue
            if value < min_val or value > max_val:
                # 범위를 벗어난 정도에 비례하여 패널티 산출
                range_span = max_val - min_val
                if value < min_val:
                    deviation = (min_val - value) / range_span
                else:
                    deviation = (value - max_val) / range_span
                penalty = min(0.5, 0.2 + deviation * 0.3)
                results.append((field, float(value), min_val, max_val, penalty))
        return results

    def _check_sudden_changes(
        self, data: dict[str, Any]
    ) -> list[tuple[str, float, float, float, float]]:
        """이전 데이터 대비 급격한 변화를 감지한다.

        Args:
            data: 검증할 데이터.

        Returns:
            (필드명, 이전값, 현재값, 한도, 패널티) 튜플 리스트.
        """
        results: list[tuple[str, float, float, float, float]] = []
        for field, limit in WEEKLY_CHANGE_LIMITS.items():
            if field not in data or field not in self._previous_data:
                continue
            value = data[field]
            if not isinstance(value, (int, float)):
                continue
            prev = self._previous_data[field]
            change = abs(float(value) - prev)
            if change > limit:
                # 초과 비율에 따라 패널티 산출
                excess_ratio = (change - limit) / limit
                penalty = min(0.4, 0.15 + excess_ratio * 0.25)
                results.append((field, prev, float(value), limit, penalty))
        return results

    def _check_impossible_combinations(
        self, data: dict[str, Any]
    ) -> list[tuple[str, float]]:
        """논리적으로 불가능한 필드 조합을 검사한다.

        Args:
            data: 검증할 데이터.

        Returns:
            (설명, 패널티) 튜플 리스트.
        """
        results: list[tuple[str, float]] = []

        # BMI 일관성 검사: BMI = weight / (height_m)^2
        if all(k in data for k in ("weight_kg", "height_cm", "bmi")):
            weight = data["weight_kg"]
            height_cm = data["height_cm"]
            bmi = data["bmi"]
            if (
                isinstance(weight, (int, float))
                and isinstance(height_cm, (int, float))
                and isinstance(bmi, (int, float))
                and height_cm > 0
            ):
                height_m = height_cm / 100.0
                expected_bmi = weight / (height_m ** 2)
                bmi_diff = abs(expected_bmi - bmi)
                if bmi_diff > 2.0:
                    results.append(
                        (
                            f"BMI {bmi} does not match weight {weight}kg / "
                            f"height {height_cm}cm (expected ~{expected_bmi:.1f})",
                            0.3,
                        )
                    )

        # 수면 + 운동 시간 합계가 24시간을 초과하는지 검사
        sleep = data.get("sleep_hours")
        exercise = data.get("exercise_hours")
        if (
            isinstance(sleep, (int, float))
            and isinstance(exercise, (int, float))
        ):
            if sleep + exercise > 24.0:
                results.append(
                    (
                        f"Sleep ({sleep}h) + Exercise ({exercise}h) "
                        f"exceeds 24 hours",
                        0.4,
                    )
                )

        return results

    def _calculate_confidence(self, penalties: list[float]) -> float:
        """패널티 목록으로부터 최종 신뢰도 점수를 산출한다.

        Args:
            penalties: 개별 검증 항목의 패널티 값 리스트 (0.0~1.0).

        Returns:
            신뢰도 점수 (0.0 ~ 1.0). 1.0이면 완벽히 정상,
            0.0이면 확실히 잘못된 데이터.
        """
        if not penalties:
            return 1.0

        # 각 패널티를 곱셈 방식으로 누적하여 신뢰도 하락
        confidence = 1.0
        for penalty in penalties:
            confidence *= (1.0 - min(penalty, 1.0))

        return max(0.0, round(confidence, 4))
