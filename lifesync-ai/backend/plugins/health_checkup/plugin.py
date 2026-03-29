"""팀원 C — 건강검진 분석 플러그인 (기본 구현 60%).

현재 구현된 기능:
    - 10개 메트릭 정상/주의/위험 3단계 분류
    - HealthGuidelinesDB 기준 범위 조회
    - GPT-4o-mini (temp=0.3) 보수적 요약

개선 가능한 영역 (팀원 C가 발전시킬 부분):
    - [ ] 메트릭 간 상관관계 분석 (혈당+콜레스테롤 복합 위험)
    - [ ] 시계열 트렌드 분석 (이전 검진과 비교)
    - [ ] 맞춤형 후속 조치 추천 (재검 주기, 전문의 추천)
    - [ ] 검진 결과 시각화 데이터 생성
    - [ ] 약물 상호작용 경고 (현재 복용 약물 고려)
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# 기본 참조 범위 (HealthGuidelinesDB 미연결 시 폴백)
_DEFAULT_RANGES = {
    "bmi": {"normal": (18.5, 24.9), "caution": (25.0, 29.9), "unit": "kg/m²"},
    "blood_sugar": {"normal": (70, 99), "caution": (100, 125), "unit": "mg/dL"},
    "cholesterol": {"normal": (0, 199), "caution": (200, 239), "unit": "mg/dL"},
    "blood_pressure_sys": {"normal": (90, 119), "caution": (120, 139), "unit": "mmHg"},
    "blood_pressure_dia": {"normal": (60, 79), "caution": (80, 89), "unit": "mmHg"},
    "hemoglobin": {"normal": (12.0, 17.5), "caution": (10.0, 11.9), "unit": "g/dL"},
    "sleep_quality": {"normal": (70, 100), "caution": (50, 69), "unit": "점"},
    "stress_level": {"normal": (0, 40), "caution": (41, 70), "unit": "점"},
    "heart_rate": {"normal": (60, 100), "caution": (50, 59), "unit": "bpm"},
    "body_fat": {"normal": (10, 25), "caution": (26, 32), "unit": "%"},
}


class CheckupHealthAgent:
    """건강검진 분석 에이전트."""

    def __init__(self):
        # ── 건강 가이드라인 DB ──
        self._health_db = None
        try:
            from backend.knowledge.health_guidelines import HealthGuidelinesDB
            self._health_db = HealthGuidelinesDB()
        except Exception as e:
            logger.warning("HealthGuidelinesDB 연결 실패: %s", e)

        # ── LLM (보수적 설정) ──
        self._chain = None
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser

            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, max_tokens=300,
                             api_key=os.getenv("OPENAI_API_KEY"))
            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "당신은 건강 상담사입니다. 검진 결과를 알기 쉽게 요약합니다.\n"
                    "주의: 의료 진단이나 처방을 하지 마세요. '~를 권장합니다' 형태로만 조언하세요."
                )),
                ("human", "다음 건강검진 결과를 3줄로 요약하고, 주의할 점을 알려주세요:\n{evaluations}"),
            ])
            self._chain = prompt | llm | StrOutputParser()
        except Exception as e:
            logger.warning("LLM 초기화 실패: %s", e)

    def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
        """검진 수치 → 분석 결과."""
        checkup = user_state.get("checkup_metrics", {})
        if not checkup:
            # 검진 데이터 없으면 기본 상태에서 추출
            checkup = {
                "bmi": user_state.get("bmi", 22),
                "sleep_quality": user_state.get("sleep_quality", 70),
                "stress_level": user_state.get("stress", 50),
            }

        # 1단계: 메트릭별 분류
        evaluations = []
        overall_risk = "normal"

        for metric, value in checkup.items():
            status, advice, ref_range = self._classify_metric(metric, value)
            evaluations.append({
                "metric": metric,
                "value": value,
                "status": status,
                "range": ref_range,
                "advice": advice,
            })
            if status == "danger":
                overall_risk = "danger"
            elif status == "caution" and overall_risk == "normal":
                overall_risk = "caution"

        # 2단계: LLM 요약
        explanation = self._generate_summary(evaluations)

        return {
            "recommendations": [e["advice"] for e in evaluations if e["status"] != "normal"],
            "risk_level": overall_risk,
            "metrics_analysis": evaluations,
            "explanation": explanation,
        }

    def _classify_metric(
        self, metric: str, value: float
    ) -> tuple[str, str, dict]:
        """수치 → 정상/주의/위험 분류."""
        # DB에서 기준 범위 조회
        ref = self._get_reference(metric)
        normal = ref.get("normal", (0, 100))
        caution = ref.get("caution", (0, 0))
        unit = ref.get("unit", "")

        if normal[0] <= value <= normal[1]:
            return "normal", f"{metric} 정상 범위입니다.", ref
        elif caution and caution[0] <= value <= caution[1]:
            return "caution", f"{metric} 수치({value}{unit})가 주의 범위입니다. 정기적 모니터링을 권장합니다.", ref
        else:
            return "danger", f"{metric} 수치({value}{unit})가 위험 범위입니다. 전문가 상담을 권장합니다.", ref

    def _get_reference(self, metric: str) -> dict:
        """기준 범위 조회. DB 없으면 기본값."""
        if self._health_db:
            try:
                ref = self._health_db.get_reference_range(metric)
                if ref:
                    return {
                        "normal": (ref.get("normal_min", 0), ref.get("normal_max", 100)),
                        "caution": (ref.get("normal_max", 100), ref.get("warning_max", 150)),
                        "unit": ref.get("unit", ""),
                    }
            except Exception:
                pass
        return _DEFAULT_RANGES.get(metric, {"normal": (0, 100), "caution": (0, 0), "unit": ""})

    def _generate_summary(self, evaluations: list[dict]) -> str:
        """LLM으로 검진 요약. 실패 시 규칙 기반."""
        if self._chain:
            try:
                eval_text = "\n".join(
                    f"{e['metric']}: {e['value']} ({e['status']})"
                    for e in evaluations
                )
                return self._chain.invoke({"evaluations": eval_text})
            except Exception as e:
                logger.warning("LLM 요약 실패: %s", e)

        # 규칙 기반 요약
        danger = [e for e in evaluations if e["status"] == "danger"]
        caution = [e for e in evaluations if e["status"] == "caution"]
        if danger:
            return f"위험 항목 {len(danger)}개 발견. 전문가 상담을 권장합니다."
        elif caution:
            return f"주의 항목 {len(caution)}개. 생활 습관 개선을 권장합니다."
        return "전체적으로 양호합니다."


def register(registry):
    """플러그인 등록."""
    try:
        agent = CheckupHealthAgent()
        registry.register("health_agent", agent)
        logger.info("health_checkup 플러그인 활성화")
    except Exception as e:
        logger.warning("health_checkup 플러그인 로드 실패: %s", e)
