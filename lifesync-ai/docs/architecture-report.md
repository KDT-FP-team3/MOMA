# LifeSync AI 아키텍처 보고서 (v0.3.0)

> 각 컴포넌트의 역할, 기능, 관계, 장단점, 필요한 이유를 설명합니다.
> v0.3.0: Router 분리 패턴 + 5개 데이터 흐름 연결 + 보안 강화 반영.

---

## 전체 아키텍처 개요

```
사용자 (웹/앱/APK)
    ↓ HTTP/WebSocket
Frontend (React 18 + Capacitor)  ←→  Offline Engine (IndexedDB)
    ↓ Vite Proxy / HTTPS
main.py (180줄: 미들웨어 + 라우터 등록만)
    ├→ ai_router.py (그룹 A: 사진/시뮬/모델)
    ├→ api_router.py (그룹 B: 쿼리/인증/대시보드/WS)
    └→ 보안: JWT + RateLimit(60/분) + 보안헤더 + 입력검증
         ↓ 라우팅
Orchestrator (LangGraph 8-node DAG)
    ↓ 도메인별 분배 + CASCADE_RULES
┌──────────┬──────────┬──────────┬──────────┐
│FoodAgent │Exercise  │Health    │Hobby     │ ← LangChain + RAG
└────┬─────┴────┬─────┴────┬─────┴────┬─────┘
     ↓          ↓          ↓          ↓
  GPT-4o-mini (LLM)  +  ChromaDB (4 컬렉션 RAG)
     ↓                        ↓
  updated_gauges → AppState → 대시보드 즉시 반영 (v0.3.0 연결)
     ↓
Reward Function → PPO Agent → Retrain → Optuna
     ↓
Supabase (상태) / S3 (모델) / Railway / Vercel / Capacitor
```

---

## Layer 0: 사용자 인터페이스

### 1. Frontend (React)
- **역할**: 사용자가 직접 상호작용하는 웹 인터페이스
- **기능**: 11개 페이지 (대시보드, 시뮬레이터, 스케줄러, 사진 분석, 로드맵 등), 다크/라이트 모드, 반응형 디자인
- **관계**: FastAPI에 HTTP/WebSocket으로 연결, Offline Engine으로 오프라인 폴백
- **장점**: React.lazy 코드 스플리팅으로 빠른 초기 로딩, Tailwind CSS로 일관된 디자인
- **단점**: SSR 미지원 (SEO 불리), 대형 페이지(SchedulePage 34KB) 존재
- **필요한 이유**: 사용자가 건강 데이터를 시각적으로 확인하고 의사결정하는 핵심 접점

### 2. Whisper STT
- **역할**: 음성을 텍스트로 변환
- **기능**: 한국어 음성 인식, 실시간 처리
- **관계**: Frontend에서 음성 데이터 수신 → 텍스트로 변환 → FastAPI로 전달
- **장점**: OpenAI Whisper 기반 높은 한국어 정확도
- **단점**: 현재 스텁 상태 (미구현), 서버 사이드 처리 시 지연 발생
- **필요한 이유**: 요리 중 손이 더러울 때, 운동 중일 때 등 음성 입력이 필수적인 상황 대응

### 3. gTTS Response
- **역할**: 텍스트를 음성으로 변환하여 응답
- **기능**: 한국어 TTS, MP3 생성
- **관계**: FastAPI에서 응답 텍스트 수신 → 음성 생성 → Frontend으로 재생
- **장점**: 무료, 한국어 지원, 경량
- **단점**: 현재 스텁 상태, 음질이 자연스럽지 않음 (기계적)
- **필요한 이유**: 시각 장애 사용자 접근성, 운동 중 화면을 볼 수 없는 상황

---

## Layer 1: 서버 인프라

### 4. FastAPI Backend
- **역할**: 모든 API 요청을 처리하는 중앙 서버
- **기능**: 30+ REST 엔드포인트, WebSocket, 파일 업로드, 보안 미들웨어
- **관계**: Frontend ↔ FastAPI ↔ 모든 백엔드 서비스
- **장점**: Python 비동기 지원, 자동 Swagger 문서, Pydantic 타입 검증
- **단점**: 단일 서버 (수평 확장 시 상태 공유 필요), main.py가 비대 (800+ 줄)
- **필요한 이유**: 프론트엔드와 AI/ML 모듈을 연결하는 유일한 통로

### 5. WebSocket
- **역할**: 실시간 양방향 통신
- **기능**: 실시간 게이지 업데이트, 음성 스트리밍, 쿼리/피드백
- **관계**: Frontend ↔ FastAPI WebSocket 엔드포인트
- **장점**: HTTP 폴링 대비 지연 시간 90% 감소, 서버 → 클라이언트 푸시 가능
- **단점**: 연결 유지 비용, 서버 재시작 시 연결 끊김
- **필요한 이유**: 대시보드 게이지가 실시간으로 변해야 사용자가 행동의 효과를 즉시 확인

### 6. Docker
- **역할**: 컨테이너 기반 서비스 오케스트레이션
- **기능**: 백엔드 + ChromaDB + 프론트엔드를 한 명령으로 실행
- **관계**: docker-compose.yml로 3개 서비스 관리
- **장점**: 환경 일관성 ("내 PC에서는 되는데" 문제 해결), 한 명령 배포
- **단점**: Docker Desktop 설치 필요, 이미지 빌드 시간
- **필요한 이유**: 6명 팀원이 동일한 개발 환경을 보장, Railway 배포에 필수

### 7. Railway Deploy
- **역할**: 클라우드 배포 플랫폼
- **기능**: GitHub 연동 자동 배포, 볼륨 마운트, Health check
- **관계**: GitHub push → 자동 빌드 → Docker 실행 → 공개 URL 제공
- **장점**: $5/월로 24시간 서버 운영, 설정 간편 (railway.toml)
- **단점**: 무료 크레딧 한정 ($5), GPU 미지원, 콜드 스타트
- **필요한 이유**: 팀원/외부인이 로컬 설치 없이 서비스를 사용할 수 있는 공유 URL

### 8. JWT Auth + Rate Limit
- **역할**: API 인증 및 남용 방지
- **기능**: Bearer 토큰 검증, 분당 60회 요청 제한, Kakao OAuth 연동
- **관계**: 모든 API 요청 전에 AuthMiddleware → RateLimitMiddleware 통과
- **장점**: 사용자별 데이터 격리, DDoS 기본 방어
- **단점**: 개발 환경에서는 비활성 (ENV=development), refresh token 미구현
- **필요한 이유**: 건강 데이터는 민감 정보이므로 인증 없는 접근 차단 필수

---

## Layer 2: 처리 엔진

### 9. Orchestrator (LangGraph)
- **역할**: 사용자 요청을 적절한 도메인 에이전트로 라우팅하고 크로스 도메인 효과 계산
- **기능**: 조건 분기 (classify_intent → 에이전트 선택), 대화 메모리 50턴, 20개 캐스케이드 룰, 평가 노드
- **관계**: FastAPI → Orchestrator → 4개 에이전트 → cascade → evaluate
- **장점**: LangGraph StateGraph로 복잡한 워크플로우를 선언적으로 관리, 크로스 도메인 연쇄 효과 자동 계산
- **단점**: 현재 직렬 실행 (병렬 에이전트 호출 미지원), 그래프 구조 변경 시 전체 테스트 필요
- **필요한 이유**: "라면 먹었다" → 건강 위험도 계산 + 추가 운동 권장 + 수면 영향 예측 등 도메인 간 연쇄 효과가 핵심 가치

### 10. Schedule Simulator
- **역할**: 24시간 스케줄을 N일간 시뮬레이션하여 건강 변화 예측
- **기능**: 15개 활동 유형별 효과, 시간대 패널티/보너스, 수면/운동/스트레스 연쇄
- **관계**: FastAPI에서 호출, 프론트엔드 SchedulePage에서 결과 시각화
- **장점**: 서버 없이도 오프라인 JS 버전으로 동작, 종합 분석(문제점/조언/리듬점수) 자동 생성
- **단점**: 결정론적 모델 (확률적 변동 없음), 개인차 미반영
- **필요한 이유**: 사용자가 "이 스케줄로 한 달 살면 어떻게 될까?"를 미리 확인

### 11. Risk Engine
- **역할**: 음식 위험도 평가 및 야식 패널티 계산
- **기능**: 베이지안 위험도 점수, 야식 -5 패널티, 이벤트 타임라인 생성
- **관계**: FastAPI에서 음식 관련 요청 시 호출, Food Agent의 RAG 결과에 위험도 부착
- **장점**: 시간대 기반 동적 위험도 (같은 음식도 23시에 먹으면 위험도 상승)
- **단점**: 규칙 기반으로 새로운 음식 패턴에 적응 못 함
- **필요한 이유**: "튀김 치킨"의 콜레스테롤 위험, "야식 라면"의 수면 영향 등 구체적 경고 제공

---

## Layer 3: 도메인 에이전트 + 강화학습

### 12. Food Agent (LangChain)
- **역할**: RAG 기반 맞춤 레시피 추천 + 영양 분석
- **기능**: ChromaDB에서 레시피 검색 → GPT-4o-mini로 3개 추천 생성, 위험도 평가, 쿼리 확장 + 리랭킹
- **관계**: Orchestrator → Food Agent → ChromaDB(RAG) + GPT-4o(LLM) + Risk Engine
- **장점**: RAG로 10만건 레시피에서 개인 맞춤 검색, LLM이 자연어로 설명
- **단점**: LLM API 비용 발생, 응답 시간 2-5초
- **필요한 이유**: "BMI 27인 사람에게 저칼로리 저녁 메뉴"처럼 개인화된 식단 추천

### 13. Exercise Agent (LangChain)
- **역할**: 맞춤 운동 추천 + 부상 위험 평가
- **기능**: 미세먼지 연동 실내 대체 운동, 부상 위험도 점수, 강도 자동 조절
- **관계**: Orchestrator → Exercise Agent → ChromaDB + GPT-4o
- **장점**: 환경(미세먼지, 날씨) 고려한 추천, 부상 이력 반영
- **단점**: 날씨 API 미연동 (스텁), 운동 자세 실시간 피드백 미구현
- **필요한 이유**: 안전하고 효과적인 운동을 위해 개인 상태 + 환경 고려 필수

### 14. Health Agent (LangChain)
- **역할**: 건강검진 분석 + 건강 개선 플랜 생성
- **기능**: 혈압/콜레스테롤/혈당 등 메트릭 분석, 위험도 분류 (low/medium/high), 맞춤 플랜
- **관계**: Orchestrator → Health Agent → GPT-4o
- **장점**: 건강검진 숫자를 알기 쉬운 자연어로 해석
- **단점**: 의료 면허 없는 AI 조언의 한계 (면책 조항 필요)
- **필요한 이유**: 건강검진 결과를 받고 "이 수치가 뭘 의미하는지" 모르는 사용자에게 가이드 제공

### 15. Hobby Agent (LangChain)
- **역할**: 스트레스 해소용 취미 추천 + 시너지 계산
- **기능**: 스트레스 수준 기반 추천, 크로스 도메인 시너지 (취미 → 폭식 충동 -40%), 감소율 모델링
- **관계**: Orchestrator → Hobby Agent → ChromaDB + GPT-4o
- **장점**: 건강과 취미를 연결하는 독창적 접근 (기타 30분 → 스트레스 -15%)
- **단점**: 취미 카탈로그가 제한적, 개인 선호도 학습 미흡
- **필요한 이유**: 건강 관리가 식단/운동만이 아니라 정신 건강(취미)도 포함해야 지속 가능

### 16. PPO Reinforcement Learning
- **역할**: 사용자 행동에 대한 최적 정책 학습
- **기능**: 40차원 상태 벡터, 10개 이산 행동, 84스텝(12주) 에피소드, Stable-Baselines3 기반
- **관계**: Schedule Simulator → PPO(정책 추론), Retrain Scheduler → PPO(재학습)
- **장점**: 사용자 피드백으로 지속 개선, 다축 보상 함수로 균형 잡힌 추천
- **단점**: CPU 학습 느림 (GPU 권장), 초기 학습 데이터 부족 시 랜덤에 가까운 정책
- **필요한 이유**: 규칙 기반 시스템은 개인차를 반영 못 함 → RL로 개인별 최적 전략 학습

### 17. Retrain Scheduler
- **역할**: RL 모델 재학습 시점을 자동 판단하고 실행
- **기능**: 6시간 주기 재학습, 보상 10% 하락 시 트리거, 피드백 점수 2.0 미만 시 트리거, 사용자별 보상 가중치
- **관계**: FastAPI(/api/feedback) → Retrain Scheduler → PPO Agent + Optuna
- **장점**: 수동 개입 없이 모델이 자동으로 개선, 사용자별 개인화 가중치
- **단점**: 백그라운드 태스크로 서버 리소스 소모, Railway에서 SB3 미설치
- **필요한 이유**: 사용자가 "이 추천은 별로"라고 피드백하면 시스템이 학습해서 다음에 더 나은 추천 제공

### 18. Optuna AutoTuner
- **역할**: PPO 하이퍼파라미터 자동 최적화
- **기능**: learning_rate, n_steps, gamma, batch_size 탐색, 100 trial, 베이지안 최적화
- **관계**: Retrain Scheduler → Optuna → 최적 파라미터 → PPO 학습
- **장점**: 수동 튜닝 대비 최적 파라미터를 체계적으로 탐색
- **단점**: 100 trial × 1000 스텝 = 상당한 연산 시간 (GPU 권장)
- **필요한 이유**: RL의 성능은 하이퍼파라미터에 극도로 민감 → 자동 탐색 필수

---

## Layer 4: AI/데이터 백엔드

### 19. GPT-4o-mini
- **역할**: 자연어 이해 및 생성 엔진
- **기능**: 에이전트 추천 생성, 건강 분석 요약, 사진 기반 개인화 조언, 인텐트 분류
- **관계**: 4개 에이전트 + PhotoAnalyzer → GPT-4o-mini API
- **장점**: 한국어 자연어 처리 우수, 맥락 이해, 창의적 추천
- **단점**: API 호출 비용 ($0.15/1M 입력 토큰), 네트워크 의존, 할루시네이션 가능
- **필요한 이유**: 규칙 기반으로는 "왜 이 레시피인지" 설명 불가 → LLM이 자연어 설명 생성

### 20. ChromaDB (RAG)
- **역할**: 벡터 유사도 기반 지식 검색
- **기능**: 4개 컬렉션 (레시피/운동/건강/취미), 다국어 임베딩, 쿼리 확장 + 컨텍스트 리랭킹
- **관계**: 4개 에이전트 → ChromaDB 쿼리 → 결과를 LLM 프롬프트에 주입
- **장점**: 무료 오픈소스, persistent 저장, 한국어 multilingual 임베딩 지원
- **단점**: 대규모 데이터(100만건+)에서 성능 저하, 하이브리드 검색(BM25) 미지원
- **필요한 이유**: LLM만으로는 최신 레시피/운동 정보를 알 수 없음 → RAG로 실시간 지식 주입

### 21. Supabase PostgreSQL
- **역할**: 사용자 상태 영속 저장
- **기능**: 40차원 State 벡터 UPSERT, pg8000 순수 Python 드라이버, 인메모리 캐시 폴백
- **관계**: FastAPI → UserStateManager → Supabase
- **장점**: 무료 플랜 (500MB), 관리형 PostgreSQL, REST API 자동 제공
- **단점**: 무료 플랜 연결 수 제한, statement timeout 발생 가능
- **필요한 이유**: 사용자가 앱을 종료하고 다시 와도 이전 건강 상태가 유지되어야 함

### 22. AWS S3 Model Storage
- **역할**: 학습된 ML 모델 가중치 저장 + 버전 관리
- **기능**: SHA256 체크섬, 버전 메타데이터, 클라이언트 동기화 API
- **관계**: GPU 학습 → S3 업로드, Railway/클라이언트 → S3 다운로드
- **장점**: 내구성 99.999999999%, 저렴한 저장 비용, 글로벌 접근
- **단점**: AWS 계정 필요, 전송 비용 발생
- **필요한 이유**: 로컬 GPU로 학습한 모델을 서버와 클라이언트가 공유하는 중앙 저장소

### 23. YOLO Food Recognition
- **역할**: 사진에서 식재료/음식 자동 인식
- **기능**: YOLOv8n 객체 감지, 신뢰도 필터링, 바운딩 박스
- **관계**: FastAPI(/api/food/recognize) → YOLO → 감지 결과
- **장점**: 실시간 추론 (CPU에서도 ~100ms), 80+ 카테고리 감지
- **단점**: 한국 음식 특화 학습 안 됨 (COCO 기본 모델), Railway에서 미설치
- **필요한 이유**: 사용자가 식단 사진을 찍으면 자동으로 칼로리/영양소 추정

### 24. OpenCLIP Embedding
- **역할**: 이미지와 텍스트를 동일 벡터 공간에 임베딩
- **기능**: ViT-B-32 모델, 512차원 벡터, 이미지-텍스트 유사도, 얼굴/체형 분석 → LLM 개인화 조언
- **관계**: FastAPI(/api/photo/upload) → CLIP 분석 → GPT-4o 개인화 조언
- **장점**: 이미지+텍스트 크로스 모달 검색 가능, lazy loading으로 메모리 효율적
- **단점**: ViT-B-32는 정확도 한계 (ViT-L-14가 더 정확하지만 GPU 필요)
- **필요한 이유**: 사진 한 장으로 건강 상태를 추정하고 맞춤 조언을 생성하는 핵심 기술

### 25. MediaPipe Pose
- **역할**: 인체 자세 분석 (33개 관절 랜드마크)
- **기능**: 어깨/척추 정렬 확인, 자세 점수, 운동별 폼 교정 (스쿼트/데드리프트/푸쉬업)
- **관계**: FastAPI → PhotoAnalyzer → PoseAnalyzer → 자세 교정 피드백
- **장점**: 무료, CPU 실시간 처리, 높은 정확도
- **단점**: 정적 이미지만 지원 (실시간 비디오 미구현), 옆모습 인식 약함
- **필요한 이유**: 잘못된 운동 자세는 부상으로 이어짐 → AI 자세 교정으로 안전한 운동

---

## Layer 5: 배포 + 오프라인

### 26. Offline Engine (JS)
- **역할**: 인터넷 없이도 시뮬레이션 및 기본 기능 제공
- **기능**: IndexedDB에 모델 가중치 캐싱, smartSimulate (온라인→서버, 오프라인→로컬 JS), 앱 시작 시 자동 동기화
- **관계**: Frontend → Offline Engine → IndexedDB, 서버 → 모델 다운로드 → IndexedDB
- **장점**: 네트워크 끊겨도 핵심 기능 사용 가능, 서버 비용 절감
- **단점**: JS 시뮬레이션은 서버 대비 단순화됨, LLM 추천은 오프라인 불가
- **필요한 이유**: 모바일 사용자는 지하철/비행기 등 오프라인 환경이 빈번 → 앱이 멈추면 안 됨

### 27. Capacitor (Android APK)
- **역할**: 웹앱을 네이티브 Android 앱으로 변환
- **기능**: 카메라 접근, 파일시스템, 오프라인 모드, Push 알림 (예정)
- **관계**: Frontend 빌드(dist/) → Capacitor sync → Android APK
- **장점**: 하나의 코드베이스로 웹+앱, 네이티브 API 접근, 앱스토어 배포 가능
- **단점**: iOS 미지원 (별도 추가 필요), 네이티브 대비 성능 약간 열세
- **필요한 이유**: "핸드폰에 직접 설치" 요구사항 충족, 사진 촬영 → 식단 분석 네이티브 경험

### 28. Vercel (Frontend Deploy)
- **역할**: 프론트엔드 정적 파일 글로벌 CDN 배포
- **기능**: GitHub 연동 자동 배포, SPA Rewrite, 글로벌 엣지 캐싱
- **관계**: GitHub push → Vercel 자동 빌드 → dist/ → CDN
- **장점**: 완전 무료, 빌드 자동화, 전 세계 빠른 로딩 (CDN)
- **단점**: 서버 사이드 로직 불가 (API는 Railway), 커스텀 도메인 SSL 제한
- **필요한 이유**: Railway는 백엔드 전용, 프론트엔드는 CDN이 훨씬 빠르고 저렴

### 29. GPU Training Pipeline
- **역할**: 로컬 GPU에서 PPO 학습 후 서버에 배포
- **기능**: Optuna 최적화 → PPO 학습 → S3/서버 업로드, CLI 스크립트
- **관계**: 로컬 GPU → train_and_upload.py → S3 → Railway/클라이언트
- **장점**: Railway의 CPU 한계를 우회, 대규모 학습 가능
- **단점**: 로컬 GPU가 있어야 함, 수동 실행 필요
- **필요한 이유**: RL 학습은 연산 집약적 → 클라우드 GPU 비용 대신 로컬 GPU 활용

---

## 연결선 카테고리 설명

| 카테고리 | 색상 | 의미 | 예시 |
|----------|------|------|------|
| **API 통신** | 파랑 | HTTP REST 요청/응답 | Frontend → FastAPI |
| **에이전트 라우팅** | 보라 | 도메인별 요청 분배 | Orchestrator → Food/Exercise/Health/Hobby |
| **LLM 추론** | 황색 | GPT-4o API 호출 | 에이전트 → GPT-4o-mini |
| **RAG 검색** | 초록 | 벡터 유사도 검색 | 에이전트 → ChromaDB |
| **데이터 저장** | 시안 | DB/스토리지 CRUD | FastAPI → Supabase, PPO → S3 |
| **비전/멀티모달** | 장미 | 이미지 처리 | FastAPI → YOLO/CLIP/MediaPipe |
| **음성 처리** | 바이올렛 | STT/TTS | Frontend → Whisper → FastAPI → gTTS |
| **강화학습** | 핑크 | RL 학습/추론 | Simulator → PPO, Retrain → Optuna |

---

## 데이터 흐름 시나리오

### 시나리오 1: "저녁에 라면 먹었어"
```
Frontend (텍스트 입력)
  → FastAPI (/api/query)
    → Orchestrator (classify_intent → "food")
      → Food Agent
        → ChromaDB (라면 관련 레시피 검색)
        → Risk Engine (야식 위험도: -5, 콜레스테롤 +12%)
        → GPT-4o-mini ("라면 대신 에어프라이어 만두를 추천드립니다")
      → Cascade Engine
        → health: 수면 -35%, 체중 +0.05kg
        → exercise: 추가 유산소 30분 권장
  → Frontend (결과 + 경고 표시)
  → Supabase (상태 업데이트)
```

### 시나리오 2: 사진 업로드 → 개인화 조언
```
Frontend (카메라 촬영)
  → FastAPI (/api/photo/upload)
    → CLIP (512차원 임베딩 → 체형: overweight, 피부: 60/100)
    → MediaPipe (자세 점수: 45/100, 라운드숄더 감지)
    → GPT-4o-mini (분석 결과 기반 Top-5 개인화 조언 생성)
  → Frontend (조언 카드 표시)
```

### 시나리오 3: 오프라인 시뮬레이션
```
Frontend (스케줄 입력 + 시뮬레이션 버튼)
  → smartSimulate() (navigator.onLine 확인)
    → [온라인] FastAPI → ScheduleSimulator (서버 연산)
    → [오프라인] offlineSimulate() (로컬 JS 연산, IndexedDB 캐시)
  → Frontend (그래프 렌더링, source: "server" | "offline" 표시)
```

---

## 기술 스택 요약

| 계층 | 기술 | 버전 |
|------|------|------|
| Frontend | React 18 + Tailwind CSS + Recharts | 18.3.1 |
| Mobile | Capacitor 8 (Android) | 8.3.0 |
| Backend | FastAPI + Uvicorn | 0.111.0 |
| AI Orchestration | LangGraph + LangChain | 0.1.1 / 0.2.1 |
| LLM | GPT-4o-mini (OpenAI) | - |
| Vector DB | ChromaDB (persistent) | 0.5.0 |
| State DB | Supabase PostgreSQL | - |
| RL | Stable-Baselines3 (PPO) + Optuna | 2.3.2 / 3.6.1 |
| Vision | OpenCLIP + MediaPipe + YOLOv8 | - |
| Storage | AWS S3 | boto3 1.34.0 |
| Deploy | Railway ($5/월) + Vercel (무료) | - |
| Container | Docker Compose | 3.9 |
