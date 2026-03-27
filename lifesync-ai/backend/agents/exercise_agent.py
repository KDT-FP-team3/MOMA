"""운동 에이전트 — LangChain 기반 운동 추천 및 부상 방지.

날씨 연동 + 플랜 자동 변경 지원.
"""

import logging
import os
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

logger = logging.getLogger(__name__)

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

EXERCISE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "운동 전문 트레이너입니다. 3개의 운동을 JSON 배열로 추천하세요.\n"
            '각 운동: {{"name": str, "duration_min": int, "calories": int, "reason": str}}',
        ),
        (
            "human",
            "BMI: {bmi}, 목표: {goal}\n참고 운동:\n{rag_context}",
        ),
    ]
)


class ExerciseAgent:
    """운동 도메인 에이전트 (LangChain 기반)."""

    def __init__(
        self,
        exercise_db: Any | None = None,
        plan_adjuster: Any | None = None,
    ) -> None:
        self._exercise_db = exercise_db
        self._plan_adjuster = plan_adjuster
        self._llm: ChatOpenAI | None = None
        self._chain: Any = None

        if OPENAI_API_KEY:
            self._llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=400,
                api_key=OPENAI_API_KEY,
            )
            self._chain = EXERCISE_PROMPT | self._llm | JsonOutputParser()

    def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
        """사용자 상태 기반 운동 추천."""
        query = self._build_query(user_state)
        rag_results: list[dict[str, Any]] = []
        if self._exercise_db:
            rag_results = self._exercise_db.search(query, n_results=5)

        pm10 = user_state.get("pm10", 0)
        adjusted = False
        adjustment_msg = ""
        if pm10 >= 76:
            adjusted = True
            adjustment_msg = (
                f"미세먼지 {pm10}㎍/㎥ (매우나쁨) — 야외 운동 차단, 실내 운동으로 전환"
            )

        injury_warnings: list[str] = []
        for result in rag_results:
            exercise_name = result.get("metadata", {}).get("name", "")
            risk = self.assess_injury_risk(exercise_name, user_state)
            if risk > 0.6:
                injury_warnings.append(
                    f"'{exercise_name}' 부상 위험 높음 ({risk:.0%})"
                )

        exercises = self._generate_recommendations(user_state, rag_results)

        return {
            "exercises": exercises,
            "rag_results": rag_results[:3],
            "adjusted": adjusted,
            "adjustment_message": adjustment_msg,
            "injury_warnings": injury_warnings,
        }

    def assess_injury_risk(
        self, exercise: str, user_profile: dict[str, Any]
    ) -> float:
        """운동별 부상 위험도 평가 (0.0 ~ 1.0)."""
        base_risk = 0.2

        if self._exercise_db:
            injury_data = self._exercise_db.get_injury_data(exercise)
            injury_risks = injury_data.get("injury_risks", [])
            difficulty = injury_data.get("difficulty", 1)
            base_risk = min(0.8, len(injury_risks) * 0.15 + difficulty * 0.05)

        age = user_profile.get("age", 30)
        if age > 50:
            base_risk *= 1.3
        elif age > 40:
            base_risk *= 1.1

        existing_injuries = user_profile.get("injuries", [])
        if "knee" in existing_injuries and exercise in ("러닝", "스쿼트", "점프스쿼트"):
            base_risk = min(1.0, base_risk + 0.3)
        if "back" in existing_injuries and exercise in ("데드리프트", "바벨로우"):
            base_risk = min(1.0, base_risk + 0.3)

        return min(1.0, base_risk)

    def _build_query(self, user_state: dict[str, Any]) -> str:
        """검색 쿼리 생성."""
        parts: list[str] = []
        goal = user_state.get("goal", "")
        if goal:
            parts.append(goal)
        fitness_level = user_state.get("fitness_level", "")
        if fitness_level:
            parts.append(f"{fitness_level} 난이도")
        pm10 = user_state.get("pm10", 0)
        if pm10 >= 76:
            parts.append("실내 운동")
        if not parts:
            parts.append("전신 운동 추천")
        return " ".join(parts)

    def _generate_recommendations(
        self,
        user_state: dict[str, Any],
        rag_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """LangChain 기반 운동 추천."""
        if not self._chain:
            return self._fallback_recommendations(rag_results)

        rag_context = "\n".join(
            f"- {r.get('metadata', {}).get('name', '')}: "
            f"{r.get('metadata', {}).get('calories_per_30min', 0)}kcal/30분, "
            f"난이도 {r.get('metadata', {}).get('difficulty', 1)}"
            for r in rag_results[:5]
        )

        try:
            result = self._chain.invoke(
                {
                    "bmi": user_state.get("bmi", 22),
                    "goal": user_state.get("goal", "전반적 체력 향상"),
                    "rag_context": rag_context or "없음",
                }
            )
            if isinstance(result, list):
                return result
            return [result]
        except Exception:
            logger.exception("LangChain 운동 추천 실패")
            return self._fallback_recommendations(rag_results)

    def _fallback_recommendations(
        self, rag_results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """폴백 추천."""
        recs: list[dict[str, Any]] = []
        for r in rag_results[:3]:
            meta = r.get("metadata", {})
            recs.append(
                {
                    "name": meta.get("name", "걷기"),
                    "duration_min": 30,
                    "calories": int(meta.get("calories_per_30min", 100)),
                    "reason": "RAG 검색 결과 기반 추천",
                }
            )
        return recs
