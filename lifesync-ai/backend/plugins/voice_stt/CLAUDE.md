# 팀원 F — Whisper STT + gTTS 음성 파이프라인 플러그인

## 담당 범위
- `plugins/voice_stt/` 폴더 내 파일만 수정
- Whisper STT 구현, gTTS 한국어 응답, 음성 명령 파싱

## 구현해야 할 인터페이스
```python
class WhisperVoiceProcessor:
    def speech_to_text(self, audio_bytes: bytes) -> str:
        """음성 바이트 → 텍스트. 한국어 지원 필수."""

    def text_to_speech(self, text: str) -> bytes:
        """텍스트 → MP3 바이트. 한국어 TTS."""
```

## 사용 가능한 코어 모듈
- `backend.voice.stt_processor` — 현재 Whisper 래퍼 (참고용)
- `backend.voice.tts_responder` — 현재 gTTS 래퍼 (참고용)
- `backend.voice.intent_classifier` — 도메인 분류 (참고용)
- `whisper` 또는 `openai.Audio` — STT
- `gtts` — Google TTS

## 제한사항
1. `plugins/voice_stt/` 밖의 파일 수정 금지
2. 오디오 입력: wav/mp3/webm만 허용, 30MB 이하
3. STT 실패 시 빈 문자열 반환 (에러 전파 금지)
4. TTS 실패 시 빈 바이트 반환 (에러 전파 금지)
5. Whisper 모델은 `base` 또는 `small` 사용 (large 금지 — 메모리 부족)
6. API 키 하드코딩 금지

## 참고 파일 (읽기 전용)
- `backend/voice/stt_processor.py` — 현재 STT 구현
- `backend/voice/tts_responder.py` — 현재 TTS 구현
- `backend/core/interfaces.py` — VoiceProcessor Protocol
- `backend/core/fallbacks.py` — BasicVoiceProcessor 폴백

## 완료 기준
1. `plugin.py`의 `register()` 주석 해제
2. `GET /api/plugins/status`에서 `voice_processor: "plugin"` 표시
3. WebSocket `/ws`에서 음성 데이터 전송 → 텍스트 변환 → 응답 음성 재생
