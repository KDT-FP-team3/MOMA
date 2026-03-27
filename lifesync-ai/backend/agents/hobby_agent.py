"""취미 에이전트 — LangChain 기반 취미 추천 및 스트레스 관리.

취미는 '선순환 엔진오일' 역할로 다른 도메인에 긍정적 영향을 전파한다.
"""

import logging
import os
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

logger = logging.getLogger(__name__)

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

HOBBY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "취미 추천 전문가입니다. 3개의 취미를 JSON 배열로 추천하세요.\n"
            '각 취미: {{"name": str, "duration_min": int, "stress_relief": float, "reason": str}}',
        ),
        (
            "human",
            "스트레스: {stress}/100, 기분: {mood}/100\n참고 취미:\n{rag_context}",
        ),
    ]
)


class HobbyAgent:
    """취미 도메인 에이전트 (LangChain 기반)."""

    def __init__(self, hobby_db: Any | None = None) -> None:
        self._hobby_db = hobby_db
        self._llm: ChatOpenAI | None = None
        self._chain: Any = None

        if OPENAI_API_KEY:
            self._llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=400,
                api_key=OPENAI_API_KEY,
            )
            self._chain = HOBBY_PROMPT | self._llm | JsonOutputParser()

    def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
        """사용자 상태 기반 취미 추천."""
        stress = user_state.get("stress_level", 50)
        mood = user_state.get("mood_score", 50)

        if stress >= 70:
            query = "스트레스 해소 진정 활동 명상 기타"
        elif stress >= 50:
            query = "가벼운 취미 활동 실내 음악 그림"
        else:
            query = "재미있는 취미 사회 활동 스포츠"

        rag_results: list[dict[str, Any]] = []
        if self._hobby_db:
            rag_results = self._hobby_db.search(query, n_results=5)

        hobbies = self._generate_recommendations(user_state, rag_results)
        synergy = self._calculate_synergy(hobbies, user_state)

        return {
            "hobbies": hobbies,
            "rag_results": rag_results[:3],
            "stress_level": stress,
            "synergy_effects": synergy,
        }

    def estimate_stress_relief(
        self, hobby: str, duration_min: int
    ) -> float:
        """취미 활동의 스트레스 해소 효과 추정 (0.0 ~ 1.0)."""
        base_relief = 0.5
        if self._hobby_db:
            base_relief = self._hobby_db.get_stress_relief_score(hobby)

        time_factor = min(1.0, duration_min / 30.0)
        diminishing = 1.0 - max(0, (duration_min - 60)) * 0.005

        return min(1.0, base_relief * time_factor * max(0.5, diminishing))

    def _generate_recommendations(
        self,
        user_state: dict[str, Any],
        rag_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """LangChain 기반 취미 추천."""
        if not self._chain:
            return self._fallback_recommendations(rag_results, user_state)

        rag_context = "\n".join(
            f"- {r.get('metadata', {}).get('name', '')}: "
            f"스트레스 해소 {r.get('metadata', {}).get('stress_relief', 0.5):.0%}"
            for r in rag_results[:5]
        )

        try:
            result = self._chain.invoke(
                {
                    "stress": user_state.get("stress_level", 50),
                    "mood": user_state.get("mood_score", 50),
                    "rag_context": rag_context or "없음",
                }
            )
            if isinstance(result, list):
                return result
            return [result]
        except Exception:
            logger.exception("LangChain 취미 추천 실패")
            return self._fallback_recommendations(rag_results, user_state)

    def _fallback_recommendations(
        self,
        rag_results: list[dict[str, Any]],
        user_state: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """폴백 추천."""
        stress = user_state.get("stress_level", 50)
        if stress >= 70:
            return [
                {"name": "명상", "duration_min": 15, "stress_relief": 0.95, "reason": "높은 스트레스 해소에 가장 효과적"},
                {"name": "기타 연주", "duration_min": 30, "stress_relief": 0.8, "reason": "집중력 향상 + 스트레스 해소"},
                {"name": "가벼운 산책", "duration_min": 20, "stress_relief": 0.7, "reason": "자연 속 기분 전환"},
            ]

        recs: list[dict[str, Any]] = []
        for r in rag_results[:3]:
            meta = r.get("metadata", {})
            recs.append(
                {
                    "name": meta.get("name", "독서"),
                    "duration_min": 30,
                    "stress_relief": meta.get("stress_relief", 0.5),
                    "reason": "맞춤 취미 추천",
                }
            )
        return recs

    def _calculate_synergy(
        self, hobbies: list[dict[str, Any]], user_state: dict[str, Any]
    ) -> dict[str, Any]:
        """취미의 다른 도메인 시너지 효과."""
        stress = user_state.get("stress_level", 50)
        food_delta = -0.4 if stress >= 70 else -0.15
        health_delta = 0.3 if stress >= 70 else 0.2

        return {
            "food": {"effect": "폭식 충동 감소", "delta": food_delta},
            "exercise": {"effect": "운동 동기부여 증가", "delta": 0.1},
            "health": {"effect": "스트레스 감소 → 전반적 건강 개선", "delta": health_delta},
        }
