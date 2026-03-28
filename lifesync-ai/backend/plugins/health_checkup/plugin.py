"""팀원 C — 건강검진 분석 + 위험도 분류 플러그인.

담당: health_guidelines RAG, 검진 수치 해석, 메트릭별 위험도, LLM 요약
구현 완료 후 register() 함수 하단 주석 해제.
"""
from typing import Any

class CheckupHealthAgent:
    """건강검진 AI 분석. TODO: 팀원 C 구현."""
    def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("팀원 C 구현 예정")

def register(registry):
    # registry.register("health_agent", CheckupHealthAgent())
    pass
