# LifeSync AI

일상 생활 크로스 도메인 통합 관리 에이전트

## 개요
4개 도메인(요리 / 운동 / 건강 / 취미)을 하나의 유기체로 통합 관리하는 AI 에이전트 시스템

## 기술 스택
- **Backend**: Python 3.11, FastAPI, WebSocket, LangGraph
- **AI/ML**: GPT-4o-mini, OpenCLIP, MediaPipe, YOLO, PPO(Stable-Baselines3), Optuna
- **Vector DB**: ChromaDB
- **State DB**: Supabase PostgreSQL
- **Voice**: Whisper STT, Web Speech API, gTTS
- **Frontend**: React, Recharts, Tailwind CSS
- **Infra**: Railway, Vercel, AWS S3, Docker Compose

## 시작하기

### Backend
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env 파일에 API 키 설정
uvicorn backend.app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 팀
6명 | 기간: 4주
