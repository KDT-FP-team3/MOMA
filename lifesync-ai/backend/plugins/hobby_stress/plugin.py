"""팀원 D — 스트레스 기반 취미 추천 + 시너지 효과 플러그인 (기본 구현 60%).

현재 구현된 기능:
    - HobbyCatalog RAG 검색
    - 스트레스 수준 기반 취미 필터링
    - 기본 크로스 도메인 시너지 계산
    - GPT-4o-mini 개인화 추천

개선 가능한 영역 (팀원 D가 발전시킬 부분):
    - [ ] 성격 유형 반영 (내향/외향 → 혼자/함께 취미)
    - [ ] 시너지 효과 그래프 순회 고도화 (2차, 3차 연쇄 효과)
    - [ ] 취미 지속성 모델 (시작 난이도, 유지 비용 고려)
    - [ ] 시간대별 추천 (저녁 → 진정 취미, 아침 → 활동적 취미)
    - [ ] 취미 이력 기반 추천 (이전에 좋아한 취미 유형 학습)
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# 기본 시너지 규칙 (CASCADE_RULES 간소화 버전)
_SYNERGY_MAP = {
    "음악": {"stress": -15, "mood": +10, "sleep": +5},
    "운동": {"stress": -20, "fitness": +15, "mood": +10},
    "독서": {"stress": -10, "focus": +15, "mood": +5},
    "요리": {"stress": -8, "nutrition": +10, "mood": +8},
    "산책": {"stress": -12, "fitness": +5, "mood": +8},
    "그림": {"stress": -12, "mood": +10, "focus": +8},
    "명상": {"stress": -25, "sleep": +15, "mood": +5},
    "게임": {"stress": -5, "mood": +15, "focus": +5},
    "원예": {"stress": -15, "mood": +10, "fitness": +3},
    "사진": {"stress": -8, "mood": +12, "focus": +5},
}


class StressHobbyAgent:
    """스트레스 맞춤 취미 추천 에이전트."""

    def __init__(self):
        # ── 취미 카탈로그 DB ──
        self._hobby_db = None
        try:
            from backend.knowledge.hobby_catalog import HobbyCatalogDB
            self._hobby_db = HobbyCatalogDB()
        except Exception as e:
            logger.warning("HobbyCatalogDB 연결 실패: %s", e)

        # ── LLM ──
        self._chain = None
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import JsonOutputParser

            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, max_tokens=400,
                             api_key=os.getenv("OPENAI_API_KEY"))
            prompt = ChatPromptTemplate.from_messages([
                ("system", "당신은 스트레스 관리 전문가입니다. 취미를 통한 스트레스 해소를 추천합니다."),
                ("human", (
                    "스트레스: {stress}/100, 기분: {mood}/100\n"
                    "검색된 취미:\n{rag_context}\n시너지 효과:\n{synergy_text}\n\n"
                    "3개 취미를 추천하세요. JSON: {{\"recommendations\": [{{\"name\": str, "
                    "\"duration\": str, \"stress_reduction\": str, \"reason\": str}}], "
                    "\"explanation\": str}}"
                )),
            ])
            self._chain = prompt | llm | JsonOutputParser()
        except Exception as e:
            logger.warning("LLM 초기화 실패: %s", e)

    def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
        """스트레스/기분 → 취미 추천 + 시너지."""
        stress = user_state.get("stress", 50)
        mood = user_state.get("mood_score", 50)

        # 1단계: 스트레스 수준에 따른 쿼리
        if stress >= 70:
            query = "스트레스 해소 진정 명상 혼자"
            min_reduction = 15
        elif stress >= 40:
            query = "가벼운 취미 기분 전환"
            min_reduction = 8
        else:
            query = "재미있는 활동 도전 사교"
            min_reduction = 3

        # 2단계: RAG 검색
        rag_results = self._search_hobbies(query)

        # 3단계: 시너지 계산
        synergies = []
        for hobby in rag_results[:5]:
            name = hobby.get("name", "")
            effects = self._calculate_synergy(name, stress)
            synergies.append({"hobby": name, "effects": effects})

        # 4단계: LLM 추천
        if self._chain:
            try:
                context = "\n".join(f"- {h.get('name', '?')}" for h in rag_results[:5])
                synergy_text = "\n".join(
                    f"- {s['hobby']}: " + ", ".join(f"{k} {v:+d}" for k, v in s["effects"].items())
                    for s in synergies if s["effects"]
                )
                result = self._chain.invoke({
                    "stress": stress,
                    "mood": mood,
                    "rag_context": context or "검색 결과 없음",
                    "synergy_text": synergy_text or "시너지 정보 없음",
                })
                return {
                    "recommendations": result.get("recommendations", []),
                    "rag_results": rag_results[:3],
                    "stress_reduction": min_reduction,
                    "synergy_effects": synergies[:3],
                    "explanation": result.get("explanation", ""),
                }
            except Exception as e:
                logger.warning("LLM 취미 추천 실패: %s", e)

        # 폴백
        return {
            "recommendations": rag_results[:3],
            "rag_results": rag_results[:3],
            "stress_reduction": min_reduction,
            "synergy_effects": synergies[:3],
            "explanation": f"스트레스 {stress} 기준 추천",
        }

    def _search_hobbies(self, query: str) -> list[dict[str, Any]]:
        """취미 카탈로그 검색."""
        if self._hobby_db is None:
            # DB 없으면 기본 목록
            return [{"name": k} for k in list(_SYNERGY_MAP.keys())[:5]]
        try:
            return self._hobby_db.search(query, n_results=10)
        except Exception as e:
            logger.warning("취미 검색 실패: %s", e)
            return [{"name": k} for k in list(_SYNERGY_MAP.keys())[:5]]

    def _calculate_synergy(
        self, hobby_name: str, stress: int
    ) -> dict[str, int]:
        """크로스 도메인 시너지 계산.

        TODO(팀원D): CASCADE_RULES 그래프 순회로 2차/3차 연쇄 효과 계산
        """
        # 기본: _SYNERGY_MAP에서 직접 효과만 반환
        for key, effects in _SYNERGY_MAP.items():
            if key in hobby_name:
                # 스트레스 높을수록 감소 효과 증폭
                amplifier = 1.0 + (stress - 50) / 100  # stress=80 → 1.3배
                return {k: int(v * amplifier) for k, v in effects.items()}
        return {}


def register(registry):
    """플러그인 등록."""
    try:
        agent = StressHobbyAgent()
        registry.register("hobby_agent", agent)
        logger.info("hobby_stress 플러그인 활성화")
    except Exception as e:
        logger.warning("hobby_stress 플러그인 로드 실패: %s", e)
