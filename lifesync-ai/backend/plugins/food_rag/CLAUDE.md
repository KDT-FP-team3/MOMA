# 팀원 A — RAG 기반 레시피 추천 플러그인

## 담당 범위
- `plugins/food_rag/` 폴더 내 파일만 수정
- ChromaDB 레시피 RAG 고도화, LangChain 프롬프트, 위험도 평가

## 구현해야 할 인터페이스
```python
class AdvancedFoodAgent:
    def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
        """반환 필수: {recommendations: list, rag_results: list, explanation: str}"""
```

## 사용 가능한 코어 모듈 (import 허용)
- `backend.knowledge.chroma_client` — ChromaDB 연결
- `backend.knowledge.recipe_db` — 레시피 컬렉션 (10만건)
- `backend.risk_engine.food_risk_scorer` — 음식 위험도 계산
- `backend.risk_engine.night_meal_penalty` — 야식 패널티
- `langchain_openai.ChatOpenAI` — GPT-4o-mini
- `langchain_core.prompts.ChatPromptTemplate`
- `langchain_core.output_parsers.JsonOutputParser`

## 제한사항
1. `plugins/food_rag/` 밖의 파일 수정 금지
2. `recommend()` 반환값에 반드시 `recommendations`, `explanation` 키 포함
3. LLM 호출 실패 시 빈 결과 반환 (에러 전파 금지)
4. ChromaDB 컬렉션명은 `"recipes"` 고정 (변경 금지)
5. API 키를 코드에 하드코딩 금지 — `os.getenv("OPENAI_API_KEY")` 사용

## 참고 파일 (읽기 전용)
- `backend/agents/food_agent.py` — 현재 FoodAgent 구현 (참고용)
- `backend/core/interfaces.py` — DomainAgent Protocol 정의
- `backend/core/fallbacks.py` — BasicFoodAgent 폴백 구현
- `data/recipes.csv` — 레시피 원본 데이터

## 완료 기준
1. `plugin.py`의 `register()` 주석 해제
2. `GET /api/plugins/status`에서 `food_agent: "plugin"` 표시
3. `/api/query`에 음식 관련 질문 시 RAG 기반 응답 반환

## 에이전트 피드백 (자동)
- 점검 시각: 2026-03-30 03:29 UTC
- 인터페이스 점검: PASS
  - 모든 인터페이스 준수
- 플러그인 상태: active (AdvancedFoodAgent)
- CASCADE 연결: food -> health, exercise (2개)
