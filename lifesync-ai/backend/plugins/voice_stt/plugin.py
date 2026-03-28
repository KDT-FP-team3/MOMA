"""팀원 F — Whisper STT + gTTS 음성 파이프라인 플러그인.

담당: Whisper STT 구현, gTTS 한국어 응답, 음성 명령 파싱
구현 완료 후 register() 함수 하단 주석 해제.
"""
from typing import Any

class WhisperVoiceProcessor:
    """Whisper + gTTS 음성 처리. TODO: 팀원 F 구현."""
    def speech_to_text(self, audio_bytes: bytes) -> str:
        raise NotImplementedError("팀원 F 구현 예정")
    def text_to_speech(self, text: str) -> bytes:
        raise NotImplementedError("팀원 F 구현 예정")

def register(registry):
    # registry.register("voice_processor", WhisperVoiceProcessor())
    pass
