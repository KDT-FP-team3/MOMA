"""음성 파이프라인 테스트."""

import pytest

from backend.voice.stt_processor import STTProcessor
from backend.voice.intent_classifier import IntentClassifier
from backend.voice.tts_responder import TTSResponder


class TestSTTProcessor:
    """STTProcessor 단위 테스트."""

    def test_init_online(self) -> None:
        """온라인 모드 초기화 테스트."""
        processor = STTProcessor(use_online=True)
        assert processor.use_online is True

    def test_init_offline(self) -> None:
        """오프라인 모드 초기화 테스트."""
        processor = STTProcessor(use_online=False)
        assert processor.use_online is False

    def test_transcribe_empty_returns_string(self) -> None:
        """빈 오디오 바이트 처리 테스트."""
        processor = STTProcessor(use_online=False)
        result = processor.transcribe(b"", "ko")
        assert isinstance(result, str)


class TestIntentClassifier:
    """IntentClassifier 단위 테스트."""

    def setup_method(self) -> None:
        """테스트 설정."""
        self.classifier = IntentClassifier()

    def test_classify_food(self) -> None:
        """음식 도메인 분류 테스트."""
        result = self.classifier.classify("오늘 저녁 메뉴 추천해줘")
        assert result["domain"] == "food"
        assert "intent" in result

    def test_classify_exercise(self) -> None:
        """운동 도메인 분류 테스트."""
        result = self.classifier.classify("오늘 운동 뭐 하면 좋을까")
        assert result["domain"] == "exercise"

    def test_classify_health(self) -> None:
        """건강 도메인 분류 테스트."""
        result = self.classifier.classify("혈압이 높은데 어떻게 해야 해")
        assert result["domain"] == "health"

    def test_classify_hobby(self) -> None:
        """취미 도메인 분류 테스트."""
        result = self.classifier.classify("스트레스 해소할 취미 추천해줘")
        assert result["domain"] == "hobby"

    def test_classify_returns_valid_domain(self) -> None:
        """분류 결과가 항상 유효한 도메인 반환."""
        result = self.classifier.classify("아무말이나 해볼게")
        assert result["domain"] in IntentClassifier.DOMAINS

    def test_route(self) -> None:
        """라우팅 테스트."""
        intent = {"domain": "exercise", "intent": "recommend"}
        domain = self.classifier.route(intent)
        assert domain == "exercise"

    def test_classify_result_structure(self) -> None:
        """분류 결과 구조 테스트."""
        result = self.classifier.classify("레시피 알려줘")
        assert "domain" in result
        assert "intent" in result
        assert "confidence" in result


class TestTTSResponder:
    """TTSResponder 단위 테스트."""

    def test_synthesize_returns_bytes(self) -> None:
        """TTS 결과가 바이트 반환."""
        responder = TTSResponder()
        result = responder.synthesize("안녕하세요")
        assert isinstance(result, bytes)
