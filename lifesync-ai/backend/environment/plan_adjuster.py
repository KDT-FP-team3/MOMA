"""플랜 조정기 — 날씨 및 환경 데이터 기반 플랜 자동 재조정."""

from typing import Any


# 야외 → 실내 대체 활동 매핑
OUTDOOR_TO_INDOOR: dict[str, str] = {
    "러닝": "트레드밀",
    "조깅": "트레드밀",
    "사이클링": "실내자전거",
    "자전거": "실내자전거",
    "등산": "계단오르기",
    "축구": "실내 HIIT",
    "농구": "실내 HIIT",
    "야외 걷기": "실내 걷기",
    "걷기": "실내 걷기",
    "야외 요가": "실내 요가",
}


class PlanAdjuster:
    """날씨 → 플랜 자동 재조정기."""

    # 야외 활동 차단 기준
    PM10_THRESHOLD = 76       # 미세먼지 76 이상이면 야외 차단
    TEMP_MIN = 0              # 0도 이하면 야외 주의
    TEMP_MAX = 35             # 35도 이상이면 야외 주의

    def adjust(
        self, plan: dict[str, Any], weather: dict[str, Any]
    ) -> dict[str, Any]:
        """날씨 정보 기반 플랜 재조정.

        Args:
            plan: 현재 운동/활동 플랜.
            weather: 날씨 + 대기질 정보.

        Returns:
            조정된 플랜 + 변경 사유.
        """
        adjustments: list[str] = []
        adjusted_plan = plan.copy()

        pm10 = weather.get("pm10", 0)
        temperature = weather.get("temperature", 20)
        weather_main = weather.get("weather_main", "Clear")

        # 미세먼지 기준 초과
        if pm10 >= self.PM10_THRESHOLD:
            if plan.get("is_outdoor", False):
                activity = plan.get("activity", "")
                alternative = self.suggest_alternative(activity, weather)
                adjusted_plan["activity"] = alternative
                adjusted_plan["is_outdoor"] = False
                adjustments.append(
                    f"미세먼지 {pm10}㎍/㎥ (매우나쁨) → "
                    f"'{activity}'을 '{alternative}'로 전환"
                )

        # 극단적 기온
        if temperature <= self.TEMP_MIN or temperature >= self.TEMP_MAX:
            if plan.get("is_outdoor", False):
                activity = plan.get("activity", "")
                alternative = self.suggest_alternative(activity, weather)
                adjusted_plan["activity"] = alternative
                adjusted_plan["is_outdoor"] = False
                adjustments.append(
                    f"기온 {temperature}°C → "
                    f"실내 활동으로 전환: '{alternative}'"
                )

        # 비/눈
        if weather_main in ("Rain", "Snow", "Thunderstorm"):
            if plan.get("is_outdoor", False):
                activity = plan.get("activity", "")
                alternative = self.suggest_alternative(activity, weather)
                adjusted_plan["activity"] = alternative
                adjusted_plan["is_outdoor"] = False
                adjustments.append(
                    f"날씨 '{weather_main}' → 실내 활동으로 전환"
                )

        adjusted_plan["adjustments"] = adjustments
        adjusted_plan["adjusted"] = bool(adjustments)

        return adjusted_plan

    def suggest_alternative(
        self, activity: str, weather: dict[str, Any]
    ) -> str:
        """날씨에 따른 대체 활동 제안.

        Args:
            activity: 원래 활동 이름.
            weather: 날씨 정보.

        Returns:
            대체 활동 이름.
        """
        return OUTDOOR_TO_INDOOR.get(activity, "실내 HIIT")
