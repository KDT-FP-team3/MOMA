"""팀원 F — Whisper STT + gTTS 음성 파이프라인 플러그인 (기본 구현 60%).

현재 구현된 기능:
    - 기존 STTProcessor 래핑 (Whisper base 모델)
    - 기존 TTSResponder 래핑 (gTTS 한국어)
    - 오디오 크기/형식 검증
    - 에러 시 빈 값 반환 (에러 전파 금지)

개선 가능한 영역 (팀원 F가 발전시킬 부분):
    - [ ] Whisper small 모델로 정확도 향상
    - [ ] 실시간 스트리밍 STT (WebSocket 청크 처리)
    - [ ] 음성 명령 파싱 (도메인 키워드 감지)
    - [ ] TTS 음질 개선 (gTTS 대안: edge-tts, Coqui TTS)
    - [ ] 오디오 전처리 (노이즈 제거, 정규화)
    - [ ] 음성 대화 세션 관리 (문맥 유지)
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# 허용 오디오 최대 크기 (30MB)
_MAX_AUDIO_SIZE = 30 * 1024 * 1024


class WhisperVoiceProcessor:
    """Whisper STT + gTTS 음성 처리기."""

    def __init__(self):
        # ── STT ──
        self._stt = None
        try:
            from backend.voice.stt_processor import STTProcessor
            # base 모델 사용 (small은 팀원F가 업그레이드)
            use_online = bool(os.getenv("OPENAI_API_KEY"))
            self._stt = STTProcessor(model_size="base", use_online=use_online)
            mode = "온라인(API)" if use_online else "오프라인(로컬)"
            logger.info("STTProcessor 초기화 (%s 모드)", mode)
        except Exception as e:
            logger.warning("STTProcessor 초기화 실패: %s", e)

        # ── TTS ──
        self._tts = None
        try:
            from backend.voice.tts_responder import TTSResponder
            self._tts = TTSResponder()
            logger.info("TTSResponder 초기화 성공")
        except Exception as e:
            logger.warning("TTSResponder 초기화 실패: %s", e)

    def speech_to_text(self, audio_bytes: bytes) -> str:
        """음성 바이트 → 한국어 텍스트.

        Args:
            audio_bytes: wav/mp3/webm 오디오 바이트 (최대 30MB)

        Returns:
            인식된 텍스트. 실패 시 빈 문자열 (에러 전파 금지).
        """
        # 크기 검증
        if len(audio_bytes) > _MAX_AUDIO_SIZE:
            logger.warning("오디오 크기 초과: %d bytes (최대 %d)", len(audio_bytes), _MAX_AUDIO_SIZE)
            return ""

        if len(audio_bytes) == 0:
            return ""

        if self._stt is None:
            logger.warning("STT 모듈 비활성")
            return ""

        try:
            text = self._stt.transcribe(audio_bytes, language="ko")
            logger.info("STT 완료: '%s' (%d bytes)", text[:50], len(audio_bytes))
            return text
        except Exception as e:
            logger.error("STT 처리 실패: %s", e)
            return ""

    def text_to_speech(self, text: str) -> bytes:
        """텍스트 → 한국어 MP3 바이트.

        Args:
            text: 변환할 한국어 텍스트

        Returns:
            MP3 오디오 바이트. 실패 시 빈 바이트 (에러 전파 금지).
        """
        if not text or not text.strip():
            return b""

        if self._tts is None:
            logger.warning("TTS 모듈 비활성")
            return b""

        try:
            audio_bytes = self._tts.synthesize(text, lang="ko")
            logger.info("TTS 완료: %d bytes ('%s...')", len(audio_bytes), text[:30])
            return audio_bytes
        except Exception as e:
            logger.error("TTS 처리 실패: %s", e)
            return b""


def register(registry):
    """플러그인 등록."""
    try:
        processor = WhisperVoiceProcessor()
        registry.register("voice_processor", processor)
        logger.info("voice_stt 플러그인 활성화")
    except Exception as e:
        logger.warning("voice_stt 플러그인 로드 실패: %s", e)
