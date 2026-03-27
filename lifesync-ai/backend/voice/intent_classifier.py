"""Intent 분류기 — 사용자 발화를 분석하여 적절한 에이전트로 라우팅."""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# 키워드 기반 도메인 분류 (폴백용)
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "food": [
        "레시피", "요리", "음식", "식단", "칼로리", "식사", "밥", "반찬",
        "메뉴", "영양", "다이어트", "먹", "배고", "간식", "야식", "아침",
        "점심", "저녁", "탄수화물", "단백질", "지방", "채소", "과일",
    ],
    "exercise": [
        "운동", "헬스", "달리기", "러닝", "스쿼트", "근력", "유산소",
        "스트레칭", "요가", "필라테스", "등산", "수영", "자전거",
        "걷기", "체력", "근육", "체중", "감량", "벌크업", "HIIT",
    ],
    "health": [
        "건강", "검진", "혈압", "혈당", "콜레스테롤", "수면", "탈모",
        "비타민", "활성산소", "피로", "스트레스", "두통", "소화",
        "면역", "BMI", "체지방", "병원", "약", "질병",
    ],
    "hobby": [
        "취미", "기타", "피아노", "그림", "독서", "명상", "게임",
        "영화", "음악", "사진", "여행", "요리취미", "뜨개질",
        "캘리그라피", "댄스", "보드게임", "정원",
    ],
}

INTENT_KEYWORDS: dict[str, list[str]] = {
    "recommend": ["추천", "알려", "뭐 먹", "뭐 하", "제안", "좋을까", "어때"],
    "analyze": ["분석", "평가", "점검", "측정", "확인", "체크"],
    "query": ["궁금", "알고 싶", "어떻게", "무엇", "왜", "설명"],
    "feedback": ["좋아", "싫어", "별로", "최고", "감사", "만족"],
}


class IntentClassifier:
    """Intent 분류 및 에이전트 라우팅."""

    DOMAINS: list[str] = ["food", "exercise", "health", "hobby"]

    def __init__(self) -> None:
        self._openai_client: Any = None
        if OPENAI_API_KEY:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=OPENAI_API_KEY)
            except ImportError:
                logger.warning("openai 패키지 미설치 — 키워드 폴백 사용")

    def classify(self, text: str) -> dict[str, Any]:
        """텍스트에서 intent와 대상 도메인 분류.

        Args:
            text: 사용자 입력 텍스트.

        Returns:
            분류 결과 (domain, intent, confidence, entities).
        """
        if self._openai_client:
            return self._classify_with_llm(text)
        return self._classify_with_keywords(text)

    def route(self, intent: dict[str, Any]) -> str:
        """분류된 intent를 적절한 에이전트로 라우팅.

        Args:
            intent: classify()의 반환값.

        Returns:
            도메인 이름 문자열.
        """
        return intent.get("domain", "food")

    def _classify_with_llm(self, text: str) -> dict[str, Any]:
        """GPT-4o-mini를 사용한 LLM 기반 분류."""
        try:
            response = self._openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "사용자의 한국어 입력을 분석하여 다음 JSON 형식으로 응답하세요:\n"
                            '{"domain": "food|exercise|health|hobby", '
                            '"intent": "recommend|analyze|query|feedback", '
                            '"entities": {"key": "value"}, '
                            '"confidence": 0.0~1.0}\n'
                            "domain은 반드시 food, exercise, health, hobby 중 하나여야 합니다."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                max_tokens=150,
                temperature=0.0,
                response_format={"type": "json_object"},
            )

            import json
            result = json.loads(response.choices[0].message.content)

            if result.get("domain") not in self.DOMAINS:
                result["domain"] = "food"
            return result
        except Exception:
            logger.exception("LLM 분류 실패 — 키워드 폴백")
            return self._classify_with_keywords(text)

    def _classify_with_keywords(self, text: str) -> dict[str, Any]:
        """키워드 기반 분류 (폴백)."""
        text_lower = text.lower()

        # 도메인 분류
        domain_scores: dict[str, int] = {d: 0 for d in self.DOMAINS}
        for domain, keywords in DOMAIN_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    domain_scores[domain] += 1

        best_domain = max(domain_scores, key=domain_scores.get)  # type: ignore[arg-type]
        best_score = domain_scores[best_domain]

        if best_score == 0:
            best_domain = "food"  # 기본 도메인

        # Intent 분류
        intent = "recommend"
        for intent_type, keywords in INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    intent = intent_type
                    break

        confidence = min(1.0, best_score * 0.3) if best_score > 0 else 0.3

        return {
            "domain": best_domain,
            "intent": intent,
            "entities": {},
            "confidence": confidence,
        }
