# 팀원 B — 운동 추천 + 날씨/미세먼지 연동 플러그인

## 담당 범위
- `plugins/exercise_weather/` 폴더 내 파일만 수정
- 운동 RAG, 날씨 API 연동, 부상 위험도 평가, 실내/실외 자동 전환

## 구현해야 할 인터페이스
```python
class WeatherExerciseAgent:
    def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
        """반환 필수: {recommendations: list, explanation: str}
        선택: {injury_warnings: list, adjustment_message: str}"""
```

## 사용 가능한 코어 모듈
- `backend.knowledge.exercise_db` — 운동 + 부상 데이터
- `backend.environment.weather_monitor` — 기상청 단기예보 + 에어코리아 대기오염 API
- `backend.environment.plan_adjuster` — 날씨 → 운동 플랜 조정
- `langchain_openai.ChatOpenAI` — GPT-4o-mini
- `langchain_core.prompts.ChatPromptTemplate`

## 제한사항
1. `plugins/exercise_weather/` 밖의 파일 수정 금지
2. 미세먼지 PM10 >= 76 시 반드시 실내 운동으로 전환
3. 부상 위험도 0.7 이상이면 해당 운동 제외 + 경고 메시지
4. 날씨 API 실패 시 기본값(맑음) 사용 (에러 전파 금지)
5. API 키 하드코딩 금지

## 참고 파일 (읽기 전용)
- `backend/agents/exercise_agent.py` — 현재 ExerciseAgent 구현
- `backend/core/interfaces.py` — DomainAgent Protocol
- `backend/core/fallbacks.py` — BasicExerciseAgent 폴백
- `data/exercises.json` — 운동 데이터

## 완료 기준
1. `plugin.py`의 `register()` 주석 해제
2. `GET /api/plugins/status`에서 `exercise_agent: "plugin"` 표시
3. 미세먼지 높은 날 실내 운동 자동 추천 동작

## 에이전트 피드백 (자동)
- 점검 시각: 2026-03-30 01:14 UTC
- 인터페이스 점검: PASS
  - 모든 인터페이스 준수
- 플러그인 상태: active (WeatherExerciseAgent)
- CASCADE 연결: exercise -> health, food (2개)
