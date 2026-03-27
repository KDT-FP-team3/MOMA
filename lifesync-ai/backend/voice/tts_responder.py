"""TTS 응답기 — 텍스트를 음성으로 변환하여 응답."""

import io
import logging
from typing import Any

logger = logging.getLogger(__name__)


class TTSResponder:
    """gTTS 기반 텍스트-음성 변환기."""

    def synthesize(self, text: str, lang: str = "ko") -> bytes:
        """텍스트를 음성 바이트로 변환.

        Args:
            text: 변환할 텍스트.
            lang: 언어 코드 (기본: "ko").

        Returns:
            MP3 형식의 오디오 바이트.
        """
        try:
            from gtts import gTTS

            tts = gTTS(text=text, lang=lang)
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            return buf.getvalue()
        except ImportError:
            logger.warning("gTTS 패키지 미설치")
            return b""
        except Exception:
            logger.exception("TTS 변환 실패")
            return b""
