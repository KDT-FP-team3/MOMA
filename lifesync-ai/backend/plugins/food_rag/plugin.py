"""팀원 A — RAG 기반 레시피 추천 플러그인.

담당 범위:
    - ChromaDB 레시피 컬렉션 고도화
    - 쿼리 확장 + 리랭킹 알고리즘 개선
    - 위험도 평가 (야식, 알레르기 등)
    - LangChain 프롬프트 최적화

구현 방법:
    1. 이 파일의 AdvancedFoodAgent 클래스를 완성하세요.
    2. recommend() 메서드가 DomainAgent 인터페이스를 만족해야 합니다.
    3. register() 함수에서 레지스트리에 등록합니다.

테스트:
    python -c "from backend.plugins.food_rag.plugin import AdvancedFoodAgent; print('OK')"

이 파일을 구현하지 않아도 BasicFoodAgent(폴백)가 동작합니다.
"""

from __future__ import annotations

from typing import Any


class AdvancedFoodAgent:
    """RAG + LLM 기반 고급 음식 추천 에이전트.

    TODO (팀원 A):
        - [ ] ChromaDB recipe_db 연결
        - [ ] 쿼리 확장 (동의어, 유사 재료)
        - [ ] 리랭킹 (사용자 BMI/칼로리 목표 반영)
        - [ ] 위험도 평가 (food_risk_scorer 연동)
        - [ ] LangChain GPT-4o-mini 프롬프트 작성
    """

    def __init__(self):
        # TODO: recipe_db, risk_scorer 초기화
        pass

    def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
        """사용자 상태 → 개인화 레시피 추천.

        Args:
            user_state: {bmi, daily_calories, allergies, goals, ...}

        Returns:
            {recommendations: [...], rag_results: [...], explanation: str}
        """
        # TODO: 여기에 RAG + LLM 로직 구현
        raise NotImplementedError("팀원 A가 구현 예정")


def register(registry):
    """레지스트리에 플러그인 등록.

    이 함수는 서버 시작 시 자동으로 호출됩니다.
    구현이 완료되면 아래 주석을 해제하세요.
    """
    # TODO: 구현 완료 후 아래 주석 해제
    # registry.register("food_agent", AdvancedFoodAgent())
    pass
