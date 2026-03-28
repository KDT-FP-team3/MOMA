# LifeSync AI — Claude Code 프로젝트 컨텍스트

## 프로젝트 개요
- 프로젝트명: LifeSync AI
- 설명: 일상 생활 크로스 도메인 통합 관리 에이전트
- 4개 도메인(요리 / 운동 / 건강 / 취미)을 하나의 유기체로 통합 관리
- 팀: 6명 | 기간: 4주 | 루트 폴더: MOMA/

## 핵심 기술 스택
- Backend: Python 3.11, FastAPI, WebSocket, LangGraph
- AI/ML: GPT-4o-mini, OpenCLIP, MediaPipe, YOLO, Stable-Baselines3(PPO), Optuna
- Vector DB: ChromaDB (persistent, Railway 볼륨 마운트)
- State DB: Supabase PostgreSQL (무료 플랜)
- Voice: Whisper STT, Web Speech API, gTTS
- Frontend: React, Recharts, Tailwind CSS
- Infra: Railway (백엔드), Vercel (프론트), AWS S3 (모델 파일)
- Container: Docker Compose

## 생성할 폴더 구조
아래 구조를 MOMA/ 루트 하단에 그대로 생성해줘.

```
MOMA/
└── lifesync-ai/
    ├── CLAUDE.md                          # 이 파일
    ├── .cursorrules                       # Cursor AI 전역 제약
    ├── .github/
    │   ├── CODEOWNERS                     # 폴더 소유권
    │   └── workflows/
    │       └── ci.yml                    # pytest 자동 실행
    ├── .vscode/
    │   ├── settings.json                 # Python 인터프리터, Black 포맷터
    │   ├── launch.json                   # FastAPI + React 디버그
    │   └── extensions.json              # 권장 익스텐션
    ├── backend/
    │   ├── app/
    │   │   └── main.py                  # FastAPI + WebSocket 진입점
    │   ├── agents/
    │   │   ├── __init__.py
    │   │   ├── food_agent.py            # 요리 에이전트
    │   │   ├── exercise_agent.py        # 운동 에이전트
    │   │   ├── health_agent.py          # 건강 에이전트
    │   │   ├── hobby_agent.py           # 취미 에이전트
    │   │   └── orchestrator.py          # 크로스 도메인 연쇄 엔진
    │   ├── voice/
    │   │   ├── __init__.py
    │   │   ├── stt_processor.py         # Whisper STT
    │   │   ├── intent_classifier.py     # Intent 분류 → 에이전트 라우팅
    │   │   └── tts_responder.py         # gTTS 응답
    │   ├── rl_engine/
    │   │   ├── __init__.py
    │   │   ├── env/
    │   │   │   └── life_env.py          # Gym Env (40+ 차원 State 벡터)
    │   │   ├── ppo_agent.py             # PPO 정책 (Stable-Baselines3)
    │   │   ├── reward_cross_domain.py   # 다축 연쇄 보상 함수
    │   │   ├── auto_tuner.py            # Optuna 하이퍼파라미터 튜닝
    │   │   └── retrain_scheduler.py     # 트리거 기반 자동 재학습
    │   ├── risk_engine/
    │   │   ├── __init__.py
    │   │   ├── food_risk_scorer.py      # 음식 위험도 (Bayesian)
    │   │   ├── night_meal_penalty.py    # 야식 패널티 계산기
    │   │   └── timeline_generator.py   # 이벤트 타임라인 생성
    │   ├── multimodal/
    │   │   ├── __init__.py
    │   │   ├── clip_embedder.py         # OpenCLIP 512차원 임베딩
    │   │   ├── photo_analyzer.py        # 얼굴 + 체형 분석
    │   │   ├── food_recognizer.py       # YOLO 식재료 인식
    │   │   └── pose_analyzer.py         # MediaPipe 자세 분석
    │   ├── knowledge/
    │   │   ├── __init__.py
    │   │   ├── chroma_client.py         # ChromaDB 클라이언트 (공통)
    │   │   ├── recipe_db.py             # 레시피 10만건 임베딩
    │   │   ├── exercise_db.py           # 운동 + 부상 데이터
    │   │   ├── health_guidelines.py     # 건강검진 가이드라인
    │   │   └── hobby_catalog.py         # 취미 카탈로그
    │   ├── environment/
    │   │   ├── __init__.py
    │   │   ├── weather_monitor.py       # AirKorea + OpenWeather API
    │   │   └── plan_adjuster.py         # 날씨 → 플랜 자동 재조정
    │   ├── dashboard/
    │   │   ├── __init__.py
    │   │   └── gauge_calculator.py      # 6개 계기판 지수 계산
    │   └── services/
    │       ├── __init__.py
    │       ├── user_state_manager.py    # 40+ 차원 State 벡터 관리
    │       └── feedback_collector.py   # 피드백 → Reward 변환
    ├── frontend/
    │   ├── public/
    │   ├── src/
    │   │   ├── components/
    │   │   │   ├── GaugePanel.jsx       # 6개 계기판
    │   │   │   ├── PhotoAnalysis.jsx    # 사진 업로드 + Top-5 UI
    │   │   │   ├── RoadmapTimeline.jsx  # 12주 로드맵
    │   │   │   ├── CascadeAlert.jsx     # 크로스 도메인 경고
    │   │   │   └── VoiceControl.jsx     # 음성 입력 + TTS (신규)
    │   │   ├── App.jsx
    │   │   └── index.jsx
    │   ├── package.json
    │   └── vite.config.js
    ├── data/
    │   ├── recipes.csv                  # 레시피 원본 (시드)
    │   ├── exercises.json               # 운동 데이터
    │   └── health_guidelines.json       # 건강검진 가이드라인
    ├── tests/
    │   ├── test_e2e_scenarios.py        # 5개 E2E 시나리오
    │   ├── test_agents.py               # 에이전트 단위 테스트
    │   ├── test_rl_engine.py            # RL 엔진 단위 테스트
    │   └── test_voice_pipeline.py       # 음성 파이프라인 테스트
    ├── requirements.txt                 # Python 의존성
    ├── railway.toml                     # Railway 배포 설정
    ├── docker-compose.yml               # 전체 서비스 컨테이너
    ├── .env.example                     # 환경변수 템플릿
    ├── .gitignore
    └── README.md
```

## 팀 분업 (3그룹 — Router 기반 충돌 방지)

### 아키텍처: main.py → Router 분리 패턴
```
main.py (공통 — 팀장만 수정. 미들웨어+라우터 등록만)
  ├→ routers/ai_router.py    ← 그룹 A 전담
  ├→ routers/api_router.py   ← 그룹 B 전담
  └→ frontend/src/           ← 그룹 C 전담
```

### 그룹 A: AI/ML 엔진 (2명)
| 담당 파일 | 역할 |
|-----------|------|
| backend/app/routers/ai_router.py | AI 엔드포인트 (사진분석, 시뮬레이션, 모델동기화) |
| backend/rl_engine/ | PPO, 보상함수, Optuna, 스케줄 시뮬레이터 |
| backend/multimodal/ | CLIP, YOLO, MediaPipe, 사진분석 |
| backend/knowledge/ | ChromaDB RAG, 레시피/운동/건강 DB |
| backend/risk_engine/ | 위험도 분석, 야식 패널티 |
| scripts/, data/ | GPU 학습 스크립트, 데이터 |

### 그룹 B: 백엔드/인프라 (2명)
| 담당 파일 | 역할 |
|-----------|------|
| backend/app/routers/api_router.py | API 엔드포인트 (쿼리, 인증, 대시보드, WebSocket) |
| backend/agents/ | Orchestrator + 4개 도메인 에이전트 (LangGraph) |
| backend/voice/ | STT, Intent 분류, TTS |
| backend/services/ | 사용자 상태, 피드백, 인증, 게이미피케이션 |
| backend/dashboard/ | 게이지 계산기 |
| backend/environment/ | 날씨 API, 플랜 조정 |
| Dockerfile, railway.toml, requirements*.txt | 배포 설정 |

### 그룹 C: 프론트엔드/모바일 (2명)
| 담당 파일 | 역할 |
|-----------|------|
| frontend/src/pages/ | 11개 페이지 컴포넌트 |
| frontend/src/components/ | 공통 UI 컴포넌트 |
| frontend/src/context/ | 상태 관리 (AppState, Theme) |
| frontend/src/services/ | 오프라인 엔진, API 클라이언트 |
| frontend/android/ | Capacitor APK 빌드 |
| frontend/package.json, vite.config.js | 빌드 설정 |

### 충돌 방지 규칙
1. **그룹 A는 ai_router.py만, 그룹 B는 api_router.py만 수정** → main.py 충돌 없음
2. **새 엔드포인트 필요 시 자기 router에 추가** → 다른 그룹 파일 건드리지 않음
3. **main.py 수정 필요 시 팀장에게 PR 요청** → 미들웨어/공통 설정만 담당
4. **각 그룹은 자기 브랜치에서 작업 → PR로 main 병합**

## 코드 컨벤션
- Python: Black 포맷터, 타입 힌트 필수, docstring Google 스타일
- JS/JSX: Prettier, 함수형 컴포넌트만, props 타입 명시
- 커밋 메시지: feat: / fix: / docs: / test: / refactor: 접두사 사용
- 환경변수: 절대 하드코딩 금지, 반드시 os.getenv() 사용

## 보상 함수 핵심 로직
R(s,a,t) = w1*r_taste + w2*r_health + w3*r_fitness + w4*r_mood + w5*r_habit
           - penalty_night - penalty_risk - penalty_skip + bonus_photo_goal

패널티 예시:
- 야식 라면 (23시): -5 → 수면 -35% → 운동 -20% → 체중 목표 +2일 지연
- 튀김 치킨:       -4 → 콜레스테롤 위험 +12%
- 미세먼지 러닝:   -4 → 활성산소 증가 → 혈액 청정도 하락

보너스 예시:
- 에어프라이어 수용: +2 → 칼로리 -40%
- 기타 연주 30분:   +2 → 스트레스 -15% → 폭식 충동 -40%
- 건강검진 이행:    +4 → 불안감 감소 → 전체 안정

## 배포 전략
- 1~2주차: 로컬 개발 + Ngrok (팀원 간 공유)
- 3주차:   Railway 배포 (통합 테스트용 공유 URL)
- 4주차:   Railway 유지 + 발표 당일만 EC2 t3.micro (프리 티어)

## 환경변수 목록 (.env)
```
OPENAI_API_KEY=
DATABASE_URL=postgresql://...supabase.co/postgres
CHROMA_PATH=/data/chroma
AIRKOREA_API_KEY=
OPENWEATHER_API_KEY=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
S3_BUCKET_NAME=lifesync-models
```

## 금지 사항 (Claude Code 전역 제약)
1. .env 파일 내용을 코드에 하드코딩하지 말 것
2. requirements.txt, docker-compose.yml을 무단으로 수정하지 말 것
   → 변경 필요 시 주석으로 이유 명시 후 팀장에게 리뷰 요청
3. orchestrator.py의 run_chain() 시그니처 변경 금지 (팀장 승인 필수)
4. main 브랜치 직접 push 금지
5. 새 라이브러리 추가 시 반드시 버전 고정 (예: langchain==0.2.1)
