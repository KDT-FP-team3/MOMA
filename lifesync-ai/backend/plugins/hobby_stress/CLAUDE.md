# 팀원 D — 스트레스 기반 취미 추천 + 시너지 효과 플러그인

## 담당 범위
- `plugins/hobby_stress/` 폴더 내 파일만 수정
- 취미-스트레스 상관관계, 크로스 도메인 시너지, 감소율 모델링

## 구현해야 할 인터페이스
```python
class StressHobbyAgent:
    def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
        """반환 필수: {recommendations: list, explanation: str}
        선택: {stress_reduction: float, synergy_effects: list}"""
```

## 사용 가능한 코어 모듈
- `backend.knowledge.hobby_catalog` — 취미 카탈로그
- `backend.agents.orchestrator` — CASCADE_RULES 참조 (읽기 전용)
- `langchain_openai.ChatOpenAI` — GPT-4o-mini
- `langchain_core.prompts.ChatPromptTemplate`

## 제한사항
1. `plugins/hobby_stress/` 밖의 파일 수정 금지
2. 스트레스 감소율은 0~100 범위로 정규화
3. 크로스 도메인 시너지 계산 시 CASCADE_RULES 형식 준수
4. 예: 기타 30분 → 스트레스 -15% → 폭식 충동 -40%
5. API 키 하드코딩 금지

## 참고 파일 (읽기 전용)
- `backend/agents/hobby_agent.py` — 현재 HobbyAgent 구현
- `backend/agents/orchestrator.py` — CASCADE_RULES 정의
- `backend/core/interfaces.py` — DomainAgent Protocol
- `backend/core/fallbacks.py` — BasicHobbyAgent 폴백

## 완료 기준
1. `plugin.py`의 `register()` 주석 해제
2. `GET /api/plugins/status`에서 `hobby_agent: "plugin"` 표시
3. 스트레스 높은 사용자에게 맞춤 취미 + 시너지 효과 응답
