"""LifeSync AI — 플러그인 인터페이스 (Protocol) 정의.

각 팀원은 이 인터페이스를 구현하여 코어에 플러그인을 연결합니다.
인터페이스를 구현하지 않은 플러그인은 코어의 폴백(기본 구현)이 동작합니다.

사용 예:
    class MyFoodAgent:
        def recommend(self, user_state: dict) -> dict:
            return {"recommendations": [...], "rag_results": [...]}

    # Orchestrator에 주입:
    orchestrator.register_agent("food", MyFoodAgent())
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


# ── 도메인 에이전트 인터페이스 ──────────────────────────────

@runtime_checkable
class DomainAgent(Protocol):
    """4개 도메인 에이전트의 공통 인터페이스.

    각 팀원이 이 Protocol을 구현하면 Orchestrator에 플러그인으로 등록 가능.
    구현하지 않으면 코어의 BasicAgent(규칙 기반)가 동작합니다.

    반환값 필수 키:
        - recommendations: list[dict]  (추천 항목 목록)
        - explanation: str             (추천 이유 설명)
    """

    def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
        """사용자 상태를 받아 추천 결과를 반환."""
        ...


# ── RAG 지식베이스 인터페이스 ──────────────────────────────

@runtime_checkable
class KnowledgeBase(Protocol):
    """ChromaDB 등 벡터 DB를 추상화하는 인터페이스.

    팀원이 RAG를 고도화할 때 이 인터페이스를 구현합니다.
    구현하지 않으면 키워드 검색 폴백이 동작합니다.
    """

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """쿼리에 대해 상위 K개 결과를 반환."""
        ...


# ── 강화학습 에이전트 인터페이스 ──────────────────────────

@runtime_checkable
class RLAgent(Protocol):
    """PPO 등 RL 모델을 추상화하는 인터페이스.

    팀원이 RL을 고도화할 때 이 인터페이스를 구현합니다.
    구현하지 않으면 규칙 기반 행동 선택이 동작합니다.
    """

    def predict(self, state: Any) -> tuple[int, float]:
        """40D 상태 벡터 → (행동 인덱스, 신뢰도)."""
        ...

    def train(self, total_timesteps: int = 10000) -> dict[str, Any]:
        """학습 실행 → 결과 반환."""
        ...


# ── 멀티모달 분석 인터페이스 ──────────────────────────────

@runtime_checkable
class ImageAnalyzer(Protocol):
    """사진 분석 (CLIP, YOLO, MediaPipe 등)을 추상화.

    팀원이 비전 모델을 고도화할 때 이 인터페이스를 구현합니다.
    구현하지 않으면 "분석 기능 준비 중" 메시지를 반환합니다.
    """

    def analyze(self, image_bytes: bytes) -> dict[str, Any]:
        """이미지 바이트 → 분석 결과 dict."""
        ...


# ── 음성 처리 인터페이스 ──────────────────────────────────

@runtime_checkable
class VoiceProcessor(Protocol):
    """STT/TTS를 추상화하는 인터페이스.

    팀원이 음성 파이프라인을 구현할 때 이 인터페이스를 사용합니다.
    구현하지 않으면 텍스트 전용 모드로 동작합니다.
    """

    def speech_to_text(self, audio_bytes: bytes) -> str:
        """음성 → 텍스트 변환."""
        ...

    def text_to_speech(self, text: str) -> bytes:
        """텍스트 → 음성 바이트 변환."""
        ...


# ── 보상 함수 인터페이스 ──────────────────────────────────

@runtime_checkable
class RewardFunction(Protocol):
    """RL 보상 함수를 추상화.

    팀원이 보상 함수를 튜닝할 때 이 인터페이스를 구현합니다.
    구현하지 않으면 기본 다축 보상 함수가 동작합니다.
    """

    def calculate(
        self, state: dict[str, Any], action: int, time_hour: int
    ) -> float:
        """상태 + 행동 + 시간 → 보상값."""
        ...
