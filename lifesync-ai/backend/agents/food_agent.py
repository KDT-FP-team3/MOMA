"""요리 에이전트 — LangChain 기반 레시피 추천 및 영양 분석.

CLIP 식재료 인식 + 위험 차단 + RAG 기반 레시피 추천.
"""

import json
import logging
import os
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

logger = logging.getLogger(__name__)

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# --- LangChain 프롬프트 템플릿 ---
RECOMMEND_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "당신은 영양 전문가입니다. 사용자의 건강 상태를 고려하여 "
            "3개의 레시피를 JSON 배열로 추천하세요.\n"
            '각 레시피: {{"name": str, "reason": str, "calories": int, "benefits": str}}',
        ),
        (
            "human",
            "사용자 BMI: {bmi}, 칼로리 목표: {calorie_target}kcal\n"
            "참고 레시피:\n{rag_context}\n"
            "주의사항: {risk_alerts}",
        ),
    ]
)

NUTRITION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "음식 항목의 총 영양 정보를 JSON으로 반환하세요:\n"
            '{{"calories": float, "protein": float, "fat": float, "carbs": float}}',
        ),
        ("human", "음식: {food_items}"),
    ]
)


class FoodAgent:
    """요리 도메인 에이전트 (LangChain 기반)."""

    def __init__(
        self,
        recipe_db: Any | None = None,
        risk_scorer: Any | None = None,
    ) -> None:
        self._recipe_db = recipe_db
        self._risk_scorer = risk_scorer
        self._llm: ChatOpenAI | None = None
        self._recommend_chain: Any = None
        self._nutrition_chain: Any = None

        if OPENAI_API_KEY:
            self._llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=500,
                api_key=OPENAI_API_KEY,
            )
            parser = JsonOutputParser()
            self._recommend_chain = RECOMMEND_PROMPT | self._llm | parser
            self._nutrition_chain = NUTRITION_PROMPT | self._llm | parser

    def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
        """사용자 상태 기반 레시피 추천.

        Args:
            user_state: 사용자 상태 벡터 또는 요청 파라미터.

        Returns:
            추천 결과 (recommendations, nutrition_summary, risk_alerts).
        """
        query = self._build_search_query(user_state)
        rag_results: list[dict[str, Any]] = []
        if self._recipe_db:
            rag_results = self._recipe_db.search(query, n_results=5)

        risk_alerts: list[str] = []
        if self._risk_scorer:
            for result in rag_results:
                name = result.get("metadata", {}).get("name", "")
                score = self._risk_scorer.score(name, user_state)
                if score > 0.6:
                    risk_alerts.append(f"'{name}' 위험도 높음 ({score:.1%})")

        recommendations = self._generate_recommendations(
            user_state, rag_results, risk_alerts
        )

        return {
            "recommendations": recommendations,
            "rag_results": rag_results[:3],
            "risk_alerts": risk_alerts,
            "query": query,
        }

    def analyze_nutrition(self, food_items: list[str]) -> dict[str, float]:
        """음식 항목의 영양 정보 분석."""
        if self._nutrition_chain:
            try:
                result = self._nutrition_chain.invoke(
                    {"food_items": ", ".join(food_items)}
                )
                return result
            except Exception:
                logger.exception("LangChain 영양 분석 실패")
        return self._analyze_fallback(food_items)

    def _build_search_query(self, user_state: dict[str, Any]) -> str:
        """검색 쿼리 생성."""
        parts: list[str] = []

        meal_type = user_state.get("meal_type", "")
        if meal_type:
            parts.append(f"{meal_type} 메뉴")

        preference = user_state.get("preference", "")
        if preference:
            parts.append(preference)

        calorie_target = user_state.get("calorie_target", 0)
        if calorie_target:
            parts.append(f"{calorie_target}kcal 이하")

        bmi = user_state.get("bmi", 0)
        if bmi > 25:
            parts.append("다이어트 저칼로리")
        elif bmi and bmi < 18.5:
            parts.append("고칼로리 영양")

        if not parts:
            parts.append("건강한 한식 추천 메뉴")

        return " ".join(parts)

    def _generate_recommendations(
        self,
        user_state: dict[str, Any],
        rag_results: list[dict[str, Any]],
        risk_alerts: list[str],
    ) -> list[dict[str, Any]]:
        """LangChain 기반 맞춤 추천 생성."""
        if not self._recommend_chain:
            return self._fallback_recommendations(rag_results)

        rag_context = "\n".join(
            f"- {r.get('metadata', {}).get('name', '')}: "
            f"{r.get('metadata', {}).get('calories', 0)}kcal"
            for r in rag_results[:5]
        )

        try:
            result = self._recommend_chain.invoke(
                {
                    "bmi": user_state.get("bmi", 22),
                    "calorie_target": user_state.get("calorie_target", 2000),
                    "rag_context": rag_context or "없음",
                    "risk_alerts": ", ".join(risk_alerts) if risk_alerts else "없음",
                }
            )
            if isinstance(result, list):
                return result
            return [result]
        except Exception:
            logger.exception("LangChain 추천 생성 실패")
            return self._fallback_recommendations(rag_results)

    def _fallback_recommendations(
        self, rag_results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """RAG 결과 기반 폴백 추천."""
        recs: list[dict[str, Any]] = []
        for r in rag_results[:3]:
            meta = r.get("metadata", {})
            recs.append(
                {
                    "name": meta.get("name", "알 수 없음"),
                    "reason": "RAG 검색 결과 기반 추천",
                    "calories": int(meta.get("calories", 0)),
                    "benefits": f"단백질 {meta.get('protein', 0)}g",
                }
            )
        return recs

    def _analyze_fallback(self, food_items: list[str]) -> dict[str, float]:
        """기본 영양 추정."""
        return {
            "calories": len(food_items) * 350.0,
            "protein": len(food_items) * 15.0,
            "fat": len(food_items) * 12.0,
            "carbs": len(food_items) * 45.0,
        }
