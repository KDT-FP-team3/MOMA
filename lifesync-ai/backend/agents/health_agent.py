"""건강 에이전트 — LangChain 기반 건강검진 분석 및 건강 관리.

활성산소, 혈액 청정도, 탈모 위험도 등을 분석한다.
"""

import logging
import os
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "건강검진 결과를 분석하여 3줄 이내로 한국어 종합 요약하세요."),
        ("human", "검진 결과:\n{evaluations}"),
    ]
)


class HealthAgent:
    """건강 도메인 에이전트 (LangChain 기반)."""

    def __init__(self, health_db: Any | None = None) -> None:
        self._health_db = health_db
        self._llm: ChatOpenAI | None = None
        self._summary_chain: Any = None

        if OPENAI_API_KEY:
            self._llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=200,
                api_key=OPENAI_API_KEY,
            )
            self._summary_chain = SUMMARY_PROMPT | self._llm | StrOutputParser()

    def analyze_checkup(
        self, checkup_data: dict[str, Any]
    ) -> dict[str, Any]:
        """건강검진 결과 분석."""
        evaluations: list[dict[str, Any]] = []
        risk_count = 0

        for metric, value in checkup_data.items():
            if isinstance(value, (int, float)) and self._health_db:
                eval_result = self._health_db.evaluate_metric(metric, value)
                evaluations.append(
                    {
                        "metric": metric,
                        "value": value,
                        "status": eval_result["status"],
                        "advice": eval_result["advice"],
                    }
                )
                if eval_result["status"] in ("warning", "danger"):
                    risk_count += 1

        summary = self._generate_summary(evaluations)

        return {
            "evaluations": evaluations,
            "risk_count": risk_count,
            "risk_level": "high" if risk_count >= 3 else "medium" if risk_count >= 1 else "low",
            "summary": summary,
        }

    def generate_health_plan(
        self, user_state: dict[str, Any]
    ) -> dict[str, Any]:
        """맞춤 건강 관리 플랜 생성."""
        concerns: list[str] = []
        stress = user_state.get("stress_level", 50)
        sleep = user_state.get("sleep_score", 50)
        bmi = user_state.get("bmi", 22)

        if stress > 60:
            concerns.append("스트레스 관리")
        if sleep < 60:
            concerns.append("수면 개선")
        if bmi > 25:
            concerns.append("체중 관리")
        if bmi and bmi < 18.5:
            concerns.append("영양 보충")

        rag_results: list[dict[str, Any]] = []
        if self._health_db and concerns:
            rag_results = self._health_db.search(
                " ".join(concerns), n_results=5
            )

        plan = self._build_plan(concerns)

        return {
            "concerns": concerns,
            "plan": plan,
            "rag_context": rag_results[:3],
        }

    def _generate_summary(self, evaluations: list[dict[str, Any]]) -> str:
        """LangChain 기반 검진 결과 종합 요약."""
        if not self._summary_chain or not evaluations:
            warnings = [e for e in evaluations if e["status"] in ("warning", "danger")]
            if not warnings:
                return "전체적으로 정상 범위입니다."
            return f"{len(warnings)}개 항목에서 주의가 필요합니다."

        eval_text = "\n".join(
            f"- {e['metric']}: {e['value']} ({e['status']}) - {e['advice']}"
            for e in evaluations
        )

        try:
            return self._summary_chain.invoke({"evaluations": eval_text})
        except Exception:
            logger.exception("LangChain 요약 생성 실패")
            return f"{len(evaluations)}개 항목 분석 완료"

    def _build_plan(self, concerns: list[str]) -> list[dict[str, Any]]:
        """건강 관리 플랜 생성."""
        plan: list[dict[str, Any]] = []

        if "스트레스 관리" in concerns:
            plan.append({"category": "stress", "action": "명상 또는 가벼운 요가 15분/일", "frequency": "매일", "expected_effect": "스트레스 -15%, 수면 질 향상"})
        if "수면 개선" in concerns:
            plan.append({"category": "sleep", "action": "취침 1시간 전 전자기기 차단, 22시 이후 식사 금지", "frequency": "매일", "expected_effect": "수면 점수 +20점"})
        if "체중 관리" in concerns:
            plan.append({"category": "weight", "action": "유산소 30분 + 식단 조절 (일 -300kcal)", "frequency": "주 5회", "expected_effect": "주당 체중 -0.5kg"})
        if "영양 보충" in concerns:
            plan.append({"category": "nutrition", "action": "고단백 식단 + 간식 추가", "frequency": "매일", "expected_effect": "BMI 정상 범위 도달"})
        if not plan:
            plan.append({"category": "maintenance", "action": "현재 상태 유지, 정기 건강검진 권장", "frequency": "월 1회", "expected_effect": "건강 상태 유지"})

        return plan
