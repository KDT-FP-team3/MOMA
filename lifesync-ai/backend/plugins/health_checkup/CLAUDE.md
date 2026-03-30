# 팀원 C — 건강검진 분석 플러그인

## 담당 범위
- `plugins/health_checkup/` 폴더 내 파일만 수정
- 건강검진 수치 해석, 메트릭별 위험도 분류, LLM 요약

## 구현해야 할 인터페이스
```python
class CheckupHealthAgent:
    def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
        """반환 필수: {recommendations: list, explanation: str}
        선택: {risk_level: str, metrics_analysis: dict}"""
```

## 사용 가능한 코어 모듈
- `backend.knowledge.health_guidelines` — 건강검진 가이드라인
- `backend.risk_engine.health_models` — 6개 건강 모델
- `langchain_openai.ChatOpenAI` — GPT-4o-mini (temp=0.3 권장)
- `langchain_core.prompts.ChatPromptTemplate`

## 제한사항
1. `plugins/health_checkup/` 밖의 파일 수정 금지
2. LLM temperature=0.3 이하 사용 (건강 정보는 보수적으로)
3. 의료 진단/처방 문구 사용 금지 — "~를 권장합니다" 형태만 사용
4. 검진 수치 범위: 정상/주의/위험 3단계로 분류
5. API 키 하드코딩 금지

## 참고 파일 (읽기 전용)
- `backend/agents/health_agent.py` — 현재 HealthAgent 구현
- `backend/core/interfaces.py` — DomainAgent Protocol
- `backend/core/fallbacks.py` — BasicHealthAgent 폴백
- `data/health_guidelines.json` — 건강검진 가이드라인 데이터

## 완료 기준
1. `plugin.py`의 `register()` 주석 해제
2. `GET /api/plugins/status`에서 `health_agent: "plugin"` 표시
3. 건강 관련 질문에 검진 수치 기반 분석 응답

## 에이전트 피드백 (자동)
- 점검 시각: 2026-03-30 01:14 UTC
- 인터페이스 점검: FAIL
  - analyze_checkup() 메서드 미구현
- 플러그인 상태: active (CheckupHealthAgent)
- CASCADE 연결: health -> exercise, food (2개)
