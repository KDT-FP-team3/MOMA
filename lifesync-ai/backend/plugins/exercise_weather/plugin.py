"""팀원 B — 운동 추천 + 날씨/미세먼지 연동 플러그인.

담당: exercise_db RAG, plan_adjuster 날씨 연동, 부상 위험 평가
구현 완료 후 register() 함수 하단 주석 해제.
"""
from typing import Any

class WeatherExerciseAgent:
    """날씨 기반 운동 추천. TODO: 팀원 B 구현."""
    def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("팀원 B 구현 예정")

def register(registry):
    # registry.register("exercise_agent", WeatherExerciseAgent())
    pass
