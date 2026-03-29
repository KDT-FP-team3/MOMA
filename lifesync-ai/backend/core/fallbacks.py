"""LifeSync AI — 폴백(기본) 구현.

팀원 플러그인이 없을 때 동작하는 규칙 기반 기본 구현입니다.
LLM/GPU/외부 API 없이 순수 Python만으로 동작합니다.

플러그인이 등록되지 않은 슬롯에 자동으로 적용됩니다.
"""

from __future__ import annotations

import random
from typing import Any


# ── 기본 도메인 에이전트 (LLM 없이 동작) ─────────────────

class BasicFoodAgent:
    """규칙 기반 음식 추천 (LLM 없이 동작).

    팀원의 FoodAgent가 없을 때 이 폴백이 사용됩니다.
    """

    HEALTHY_MEALS = [
        {"name": "현미밥 + 된장찌개", "calories": 450, "category": "한식"},
        {"name": "닭가슴살 샐러드", "calories": 350, "category": "다이어트"},
        {"name": "연어 아보카도 포케", "calories": 520, "category": "건강식"},
        {"name": "두부 야채 볶음", "calories": 300, "category": "저칼로리"},
        {"name": "오트밀 + 과일", "calories": 380, "category": "아침식사"},
    ]

    def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
        bmi = user_state.get("bmi", 22)
        # BMI에 따라 칼로리 필터링
        max_cal = 400 if bmi > 25 else 600
        filtered = [m for m in self.HEALTHY_MEALS if m["calories"] <= max_cal]
        picks = random.sample(filtered or self.HEALTHY_MEALS, min(3, len(filtered or self.HEALTHY_MEALS)))
        return {
            "recommendations": picks,
            "rag_results": [],
            "explanation": f"BMI {bmi:.1f} 기준 {max_cal}kcal 이하 추천 (기본 모드)",
        }


class BasicExerciseAgent:
    """규칙 기반 운동 추천."""

    EXERCISES = [
        {"name": "걷기 30분", "intensity": "low", "calories_burn": 150},
        {"name": "조깅 20분", "intensity": "medium", "calories_burn": 250},
        {"name": "스트레칭 15분", "intensity": "low", "calories_burn": 80},
        {"name": "실내 자전거 30분", "intensity": "medium", "calories_burn": 300},
        {"name": "플랭크 10분", "intensity": "high", "calories_burn": 120},
    ]

    def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
        stress = user_state.get("stress", 50)
        # 스트레스 높으면 저강도
        intensity = "low" if stress > 70 else "medium"
        filtered = [e for e in self.EXERCISES if e["intensity"] == intensity]
        picks = random.sample(filtered or self.EXERCISES, min(3, len(filtered or self.EXERCISES)))
        return {
            "recommendations": picks,
            "rag_results": [],
            "explanation": f"스트레스 {stress} 기준 {intensity} 강도 추천 (기본 모드)",
        }


class BasicHealthAgent:
    """규칙 기반 건강 분석."""

    def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
        return self.analyze_checkup(user_state)

    def analyze_checkup(self, user_state: dict[str, Any]) -> dict[str, Any]:
        """오케스트레이터가 호출하는 건강 분석 메서드."""
        bmi = user_state.get("bmi", 22)
        sleep = user_state.get("sleep_quality", 70)
        alerts = []
        if bmi > 25:
            alerts.append("BMI가 과체중 범위입니다. 식이 조절을 권장합니다.")
        if sleep < 60:
            alerts.append("수면 품질이 낮습니다. 취침 전 카페인을 피하세요.")
        return {
            "recommendations": alerts or ["현재 건강 상태가 양호합니다."],
            "rag_results": [],
            "explanation": f"BMI {bmi:.1f}, 수면 {sleep} 기준 분석 (기본 모드)",
        }


class BasicHobbyAgent:
    """규칙 기반 취미 추천."""

    HOBBIES = [
        {"name": "독서", "stress_reduction": 15, "category": "실내"},
        {"name": "산책", "stress_reduction": 20, "category": "실외"},
        {"name": "음악 감상", "stress_reduction": 18, "category": "실내"},
        {"name": "요리", "stress_reduction": 12, "category": "실내"},
        {"name": "그림 그리기", "stress_reduction": 16, "category": "실내"},
    ]

    def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
        stress = user_state.get("stress", 50)
        # 스트레스 높으면 감소 효과 큰 것 우선
        sorted_h = sorted(self.HOBBIES, key=lambda h: h["stress_reduction"], reverse=True)
        picks = sorted_h[:3] if stress > 60 else random.sample(self.HOBBIES, 3)
        return {
            "recommendations": picks,
            "rag_results": [],
            "explanation": f"스트레스 {stress} 기준 추천 (기본 모드)",
        }


# ── 기본 RL (규칙 기반 행동 선택) ────────────────────────

class BasicRLAgent:
    """규칙 기반 행동 선택 (PPO 없이 동작).

    ACTION_MAP:
        0=건강식, 1=불건강식, 2=식사건너뛰기,
        3=유산소, 4=근력, 5=운동건너뛰기,
        6=건강체크, 7=수면최적화, 8=취미, 9=휴식
    """

    def predict(self, state: Any) -> tuple[int, float]:
        # 간단한 규칙: 항상 건강식(0) + 유산소(3) 반복
        import time
        hour = time.localtime().tm_hour
        if hour < 9:
            return (0, 0.5)   # 아침: 건강식
        elif hour < 12:
            return (3, 0.5)   # 오전: 유산소
        elif hour < 14:
            return (0, 0.5)   # 점심: 건강식
        elif hour < 18:
            return (4, 0.5)   # 오후: 근력운동
        elif hour < 21:
            return (8, 0.5)   # 저녁: 취미
        else:
            return (7, 0.5)   # 밤: 수면최적화

    def train(self, total_timesteps: int = 10000) -> dict[str, Any]:
        return {"status": "skipped", "reason": "기본 규칙 모드 (PPO 미설치)"}


# ── 기본 이미지 분석 ─────────────────────────────────────

class BasicImageAnalyzer:
    """이미지 분석 폴백 (CLIP/YOLO 없이 동작)."""

    def analyze(self, image_bytes: bytes) -> dict[str, Any]:
        return {
            "status": "basic_mode",
            "message": "이미지 분석 모델이 로드되지 않았습니다. 텍스트 입력을 이용해주세요.",
            "size_bytes": len(image_bytes),
        }


# ── 기본 음성 처리 ───────────────────────────────────────

class BasicVoiceProcessor:
    """음성 처리 폴백 (Whisper/gTTS 없이 동작)."""

    def speech_to_text(self, audio_bytes: bytes) -> str:
        return "[음성 인식 모듈이 비활성 상태입니다. 텍스트로 입력해주세요.]"

    def text_to_speech(self, text: str) -> bytes:
        return b""  # 빈 오디오 바이트


# ── 기본 지식베이스 ──────────────────────────────────────

class BasicKnowledgeBase:
    """키워드 기반 검색 폴백 (ChromaDB 없이 동작)."""

    def __init__(self, data: list[dict[str, Any]] | None = None):
        self._data = data or []

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        query_lower = query.lower()
        scored = []
        for item in self._data:
            text = str(item.get("text", "")).lower()
            score = sum(1 for word in query_lower.split() if word in text)
            if score > 0:
                scored.append({**item, "score": score})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
