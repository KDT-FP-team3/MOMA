"""팀원 B — 운동 추천 + 날씨/미세먼지 연동 플러그인 (기본 구현 60%).

현재 구현된 기능:
    - WeatherMonitor로 실시간 날씨/미세먼지 조회
    - PM10 >= 76 시 실내 운동 자동 전환
    - ExerciseDB RAG 검색
    - 기본 부상 위험도 계산

개선 가능한 영역 (팀원 B가 발전시킬 부분):
    - [ ] 날씨 예보 기반 사전 계획 (내일 비 → 오늘 실외 운동 권장)
    - [ ] 부상 위험도 정밀화 (운동별 관절/근육 매핑)
    - [ ] 시간대별 운동 추천 (아침 유산소, 저녁 근력)
    - [ ] 운동 조합 추천 (유산소 + 스트레칭 세트)
    - [ ] 날씨 API 캐싱 (동일 위치 10분 캐시)
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class WeatherExerciseAgent:
    """날씨 기반 운동 추천 에이전트."""

    # 부상 위험 가중치
    _AGE_RISK = {50: 0.3, 40: 0.1}  # 나이 >= key → +value
    _INJURY_KEYWORDS = {"무릎": 0.3, "허리": 0.3, "어깨": 0.2, "발목": 0.2}

    def __init__(self):
        # ── 운동 DB ──
        self._exercise_db = None
        try:
            from backend.knowledge.exercise_db import ExerciseDB
            self._exercise_db = ExerciseDB()
        except Exception as e:
            logger.warning("ExerciseDB 연결 실패: %s", e)

        # ── 날씨 모니터 ──
        self._weather = None
        try:
            from backend.environment.weather_monitor import WeatherMonitor
            self._weather = WeatherMonitor()
        except Exception as e:
            logger.warning("WeatherMonitor 초기화 실패: %s", e)

        # ── LLM ──
        self._chain = None
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import JsonOutputParser

            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, max_tokens=400,
                             api_key=os.getenv("OPENAI_API_KEY"))
            prompt = ChatPromptTemplate.from_messages([
                ("system", "당신은 운동 전문가입니다. 날씨와 사용자 상태를 고려하여 안전한 운동을 추천합니다."),
                ("human", (
                    "사용자: BMI {bmi}, 목표: {goal}\n날씨: {weather_note}\n"
                    "검색된 운동:\n{rag_context}\n부상 이력: {injuries}\n\n"
                    "3개 운동을 추천하세요. JSON: {{\"recommendations\": [{{\"name\": str, "
                    "\"duration\": str, \"reason\": str}}], \"explanation\": str}}"
                )),
            ])
            self._chain = prompt | llm | JsonOutputParser()
        except Exception as e:
            logger.warning("LLM 초기화 실패: %s", e)

    def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
        """날씨 + 사용자 상태 → 운동 추천."""
        bmi = user_state.get("bmi", 22)
        injuries = user_state.get("injury_history", [])
        age = user_state.get("age", 30)

        # 1단계: 날씨 확인
        weather = self._get_weather()
        pm10 = weather.get("pm10", 30)
        temp = weather.get("temperature", 20)
        is_indoor_only = pm10 >= 76 or temp < -5 or temp > 38

        # 2단계: 운동 검색
        rag_results = self._search_exercises(is_indoor_only, user_state)

        # 3단계: 부상 위험 필터링
        filtered, injury_warnings = self._filter_by_injury(rag_results, age, injuries)

        # 4단계: 날씨 보정 메시지
        adjustment_msg = self._build_adjustment_message(pm10, temp, is_indoor_only)

        # 5단계: LLM 추천
        if self._chain and filtered:
            try:
                context = "\n".join(f"- {e.get('name', '?')}" for e in filtered[:5])
                result = self._chain.invoke({
                    "bmi": bmi,
                    "goal": user_state.get("fitness_goal", "체력 향상"),
                    "weather_note": f"PM10: {pm10}, 기온: {temp}°C",
                    "rag_context": context,
                    "injuries": ", ".join(injuries) or "없음",
                })
                return {
                    "recommendations": result.get("recommendations", []),
                    "rag_results": filtered[:3],
                    "adjustment_message": adjustment_msg,
                    "injury_warnings": injury_warnings,
                    "explanation": result.get("explanation", ""),
                }
            except Exception as e:
                logger.warning("LLM 운동 추천 실패: %s", e)

        # 폴백
        return {
            "recommendations": filtered[:3],
            "rag_results": filtered[:3],
            "adjustment_message": adjustment_msg,
            "injury_warnings": injury_warnings,
            "explanation": f"PM10={pm10}, 기온={temp}°C 기준 추천",
        }

    _weather_cache: dict[str, Any] | None = None
    _weather_cache_time: float = 0

    def _get_weather(self) -> dict[str, Any]:
        """날씨 조회. 10분 캐시 + event loop 재사용."""
        import time
        now = time.time()

        # 캐시 유효 (10분)
        if self._weather_cache and now - self._weather_cache_time < 600:
            return self._weather_cache

        if self._weather is None:
            return {"pm10": 30, "temperature": 20}

        try:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                # 이미 실행 중인 loop → 비동기 컨텍스트에서 호출된 경우
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = pool.submit(
                        asyncio.run, self._weather.get_combined()
                    ).result(timeout=15)
            except RuntimeError:
                # 실행 중인 loop 없음 → 직접 실행
                result = asyncio.run(self._weather.get_combined())

            self._weather_cache = result
            self._weather_cache_time = now
            return result
        except Exception as e:
            logger.warning("날씨 조회 실패 (기본값 사용): %s", e)
            return {"pm10": 30, "temperature": 20}

    def _search_exercises(
        self, indoor_only: bool, user_state: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """운동 DB 검색."""
        if self._exercise_db is None:
            return []
        try:
            if indoor_only:
                return self._exercise_db.get_indoor_exercises()
            query = user_state.get("exercise_preference", "일반 운동")
            return self._exercise_db.search(query, n_results=10)
        except Exception as e:
            logger.warning("운동 검색 실패: %s", e)
            return []

    def _filter_by_injury(
        self, exercises: list[dict], age: int, injuries: list[str]
    ) -> tuple[list[dict], list[str]]:
        """부상 위험도 기반 필터."""
        filtered, warnings = [], []
        base_risk = sum(v for k, v in self._AGE_RISK.items() if age >= k)

        for ex in exercises:
            risk = base_risk
            name = ex.get("name", "").lower()
            for keyword, weight in self._INJURY_KEYWORDS.items():
                if keyword in " ".join(injuries):
                    # TODO(팀원B): 운동별 관절/근육 매핑으로 정밀화
                    risk += weight
            if risk >= 0.7:
                warnings.append(f"{ex.get('name', '?')}: 부상 위험 {risk:.0%}")
            else:
                filtered.append(ex)
        return filtered, warnings

    def _build_adjustment_message(
        self, pm10: int, temp: float, indoor_only: bool
    ) -> str:
        """날씨 보정 메시지."""
        parts = []
        if pm10 >= 76:
            parts.append(f"미세먼지 나쁨(PM10={pm10}) → 실내 운동 권장")
        if temp < -5:
            parts.append(f"한파(기온={temp}°C) → 실내 운동 권장")
        elif temp > 38:
            parts.append(f"폭염(기온={temp}°C) → 실내 운동 권장")
        if not parts:
            parts.append("날씨 양호 → 실내/실외 모두 가능")
        return " | ".join(parts)


def register(registry):
    """플러그인 등록."""
    try:
        agent = WeatherExerciseAgent()
        registry.register("exercise_agent", agent)
        logger.info("exercise_weather 플러그인 활성화")
    except Exception as e:
        logger.warning("exercise_weather 플러그인 로드 실패: %s", e)
