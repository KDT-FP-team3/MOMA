"""Whisper STT 프로세서 — 음성을 텍스트로 변환.

온라인 모드(OpenAI API)와 오프라인 모드(local Whisper)를 지원한다.
"""

import io
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")


class STTProcessor:
    """Whisper 기반 음성-텍스트 변환기.

    Attributes:
        model_size: 로컬 Whisper 모델 크기 ("tiny" | "base" | "small" | "medium").
        use_online: True이면 OpenAI API 사용, False이면 로컬 모델 사용.
    """

    def __init__(
        self,
        model_size: str = "base",
        use_online: bool | None = None,
    ) -> None:
        self.model_size = model_size
        self.use_online = (
            use_online if use_online is not None else bool(OPENAI_API_KEY)
        )
        self._model: Any = None

        if not self.use_online:
            self._load_local_model()

    def _load_local_model(self) -> None:
        """로컬 Whisper 모델 로드."""
        try:
            import whisper
            self._model = whisper.load_model(self.model_size)
            logger.info("로컬 Whisper 모델 로드 완료: size=%s", self.model_size)
        except ImportError:
            logger.warning("whisper 패키지 미설치 — STT 비활성화")
        except Exception:
            logger.exception("Whisper 모델 로드 실패")

    def transcribe(self, audio_bytes: bytes, language: str = "ko") -> str:
        """오디오 바이트를 텍스트로 변환.

        Args:
            audio_bytes: 오디오 데이터 (WAV/MP3 바이트).
            language: 인식 대상 언어 코드 (기본: "ko").

        Returns:
            인식된 텍스트 문자열.
        """
        if self.use_online:
            return self._transcribe_online(audio_bytes, language)
        return self._transcribe_offline(audio_bytes, language)

    def _transcribe_online(self, audio_bytes: bytes, language: str) -> str:
        """OpenAI Whisper API를 사용한 온라인 STT."""
        try:
            from openai import OpenAI

            client = OpenAI(api_key=OPENAI_API_KEY)
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
            )
            return response.text
        except ImportError:
            logger.warning("openai 패키지 미설치")
            return ""
        except Exception:
            logger.exception("온라인 STT 실패")
            return ""

    def _transcribe_offline(self, audio_bytes: bytes, language: str) -> str:
        """로컬 Whisper 모델을 사용한 오프라인 STT."""
        if self._model is None:
            logger.warning("로컬 Whisper 모델 미로드")
            return ""

        try:
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
                tmp.write(audio_bytes)
                tmp.flush()
                result = self._model.transcribe(tmp.name, language=language)
            return result["text"]
        except Exception:
            logger.exception("오프라인 STT 실패")
            return ""
