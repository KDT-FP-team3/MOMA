"""팀원 A — RAG 기반 레시피 추천 플러그인 (기본 구현 60%).

현재 구현된 기능:
    - ChromaDB recipe_db 벡터 검색
    - 사용자 BMI/칼로리 기반 기본 리랭킹
    - GPT-4o-mini로 추천 설명 생성
    - 위험도 기본 필터링

개선 가능한 영역 (팀원 A가 발전시킬 부분):
    - [ ] 쿼리 확장 알고리즘 (동의어, 유사 재료, 계절 반영)
    - [ ] 리랭킹 고도화 (알레르기, 선호도, 최근 식사 이력 반영)
    - [ ] 위험도 평가 정밀화 (조리법별 위험도, 개인 건강 상태 반영)
    - [ ] 프롬프트 최적화 (JSON 출력 안정성, 한국어 품질)
    - [ ] 캐싱 전략 (동일 쿼리 반복 방지)
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class AdvancedFoodAgent:
    """RAG + LLM 기반 음식 추천 에이전트.

    코어 모듈을 조합하여 개인화된 레시피를 추천합니다.
    LLM/DB 연결 실패 시 규칙 기반 폴백으로 동작합니다.
    """

    def __init__(self):
        # ── ChromaDB 레시피 DB ──
        self._recipe_db = None
        try:
            from backend.knowledge.recipe_db import RecipeDB
            self._recipe_db = RecipeDB()
            logger.info("RecipeDB 연결 성공")
        except Exception as e:
            logger.warning("RecipeDB 연결 실패 (키워드 검색 모드): %s", e)

        # ── 위험도 평가기 ──
        self._risk_scorer = None
        try:
            from backend.risk_engine.food_risk_scorer import FoodRiskScorer
            self._risk_scorer = FoodRiskScorer()
        except Exception as e:
            logger.warning("FoodRiskScorer 로드 실패: %s", e)

        # ── LLM 체인 ──
        self._chain = None
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import JsonOutputParser

            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=400,
                api_key=os.getenv("OPENAI_API_KEY"),
            )
            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "당신은 영양 전문가입니다. 사용자의 건강 상태에 맞는 레시피를 추천합니다.\n"
                    "반드시 JSON 형식으로 응답하세요."
                )),
                ("human", (
                    "사용자 BMI: {bmi}, 칼로리 목표: {calorie_target}kcal\n"
                    "검색된 레시피:\n{rag_context}\n"
                    "위험 경고: {risk_alerts}\n\n"
                    "위 정보를 바탕으로 3개 레시피를 추천하세요.\n"
                    "JSON: {{\"recommendations\": [{{\"name\": str, \"calories\": int, "
                    "\"reason\": str}}], \"explanation\": str}}"
                )),
            ])
            self._chain = prompt | llm | JsonOutputParser()
            logger.info("LLM 체인 초기화 성공")
        except Exception as e:
            logger.warning("LLM 체인 초기화 실패 (규칙 모드): %s", e)

    def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
        """사용자 상태 → 개인화 레시피 추천.

        Args:
            user_state: {bmi, daily_calories, goals, allergies, ...}

        Returns:
            {recommendations: list, rag_results: list, explanation: str}
        """
        bmi = user_state.get("bmi", 22)
        calorie_target = user_state.get("calorie_target", 2000)
        if bmi > 25:
            calorie_target = min(calorie_target, 1800)

        # 1단계: RAG 검색
        rag_results = self._search_recipes(user_state, calorie_target)

        # 2단계: 위험도 필터링
        filtered, risk_alerts = self._filter_by_risk(rag_results, user_state)

        # 3단계: LLM 추천 생성
        if self._chain:
            try:
                context = "\n".join(
                    f"- {r.get('name', '?')}: {r.get('calories', '?')}kcal"
                    for r in filtered[:5]
                )
                result = self._chain.invoke({
                    "bmi": bmi,
                    "calorie_target": calorie_target,
                    "rag_context": context or "검색 결과 없음",
                    "risk_alerts": ", ".join(risk_alerts) or "없음",
                })
                return {
                    "recommendations": result.get("recommendations", []),
                    "rag_results": filtered[:3],
                    "explanation": result.get("explanation", ""),
                }
            except Exception as e:
                logger.warning("LLM 추천 실패, 규칙 모드 사용: %s", e)

        # LLM 실패 시 규칙 기반 폴백
        return {
            "recommendations": filtered[:3],
            "rag_results": filtered[:3],
            "explanation": f"BMI {bmi:.1f} 기준 {calorie_target}kcal 이하 추천",
        }

    def _search_recipes(
        self, user_state: dict[str, Any], calorie_target: int
    ) -> list[dict[str, Any]]:
        """ChromaDB에서 레시피 검색. DB 없으면 빈 리스트."""
        if self._recipe_db is None:
            return []
        try:
            # TODO(팀원A): 쿼리 확장 알고리즘 개선
            query = user_state.get("diet_preference", "건강한 식사")
            context = {"calorie_target": calorie_target, "bmi": user_state.get("bmi", 22)}
            results = self._recipe_db.search(query, n_results=10, context=context)
            return results
        except Exception as e:
            logger.warning("레시피 검색 실패: %s", e)
            return []

    def _filter_by_risk(
        self, recipes: list[dict[str, Any]], user_state: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """위험도 기반 필터링. 0.6 이상이면 제외 + 경고."""
        if self._risk_scorer is None or not recipes:
            return recipes, []

        filtered = []
        alerts = []
        for recipe in recipes:
            try:
                name = recipe.get("name", "")
                score = self._risk_scorer.score(name, user_state)
                if score >= 0.6:
                    # TODO(팀원A): 대체 레시피 추천 로직 추가
                    factors = self._risk_scorer.get_risk_factors(name)
                    alerts.append(f"{name}: {', '.join(factors)}")
                else:
                    recipe["risk_score"] = score
                    filtered.append(recipe)
            except Exception:
                filtered.append(recipe)
        return filtered, alerts


def register(registry):
    """플러그인 등록. 서버 시작 시 자동 호출."""
    try:
        agent = AdvancedFoodAgent()
        registry.register("food_agent", agent)
        logger.info("food_rag 플러그인 활성화")
    except Exception as e:
        logger.warning("food_rag 플러그인 로드 실패: %s", e)
