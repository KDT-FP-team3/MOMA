"""팀원 E — 한국 음식 특화 YOLO + CLIP 플러그인 (기본 구현 60%).

현재 구현된 기능:
    - 기존 FoodRecognizer(YOLO) 래핑
    - CLIPEmbedder로 유사도 검색
    - 기본 한국어 이름 매핑 (50개)
    - 영양정보 추정 (CLIP → RecipeDB 매칭)

개선 가능한 영역 (팀원 E가 발전시킬 부분):
    - [ ] YOLO 한식 파인튜닝 (AI Hub/Roboflow 데이터셋)
    - [ ] 한국어 이름 매핑 확장 (50개 → 200+개)
    - [ ] 음식 양 추정 (객체 크기 → 그램 변환)
    - [ ] 멀티 음식 인식 (한 접시에 여러 반찬)
    - [ ] CLIP ViT-L-14 업그레이드 (GPU 환경)
    - [ ] MediaPipe 자세 분석 연동 (운동 폼 교정)
"""

from __future__ import annotations

import io
import logging
from typing import Any

logger = logging.getLogger(__name__)

# 기본 한국어 이름 매핑 (팀원E가 확장할 부분)
_KOREAN_NAMES = {
    "rice": "밥", "egg": "계란", "bread": "빵", "chicken": "닭고기",
    "beef": "소고기", "pork": "돼지고기", "fish": "생선", "shrimp": "새우",
    "tofu": "두부", "noodle": "국수", "soup": "국/찌개", "salad": "샐러드",
    "tomato": "토마토", "cucumber": "오이", "onion": "양파", "garlic": "마늘",
    "carrot": "당근", "potato": "감자", "apple": "사과", "banana": "바나나",
    "orange": "오렌지", "milk": "우유", "cheese": "치즈", "butter": "버터",
    "pizza": "피자", "hamburger": "햄버거", "sandwich": "샌드위치",
    "cake": "케이크", "cookie": "쿠키", "chocolate": "초콜릿",
    "coffee": "커피", "tea": "차", "juice": "주스", "water": "물",
    "kimchi": "김치", "bibimbap": "비빔밥", "bulgogi": "불고기",
    "tteokbokki": "떡볶이", "samgyeopsal": "삼겹살", "jjigae": "찌개",
    "gimbap": "김밥", "ramyeon": "라면", "fried_chicken": "치킨",
    "japchae": "잡채", "pajeon": "파전", "sundubu": "순두부",
    "galbi": "갈비", "naengmyeon": "냉면", "mandu": "만두",
    "jjajangmyeon": "짜장면", "tangsuyuk": "탕수육", "kimbap": "김밥",
}

# 기본 칼로리 추정 (100g 기준)
_APPROX_CALORIES = {
    "밥": 130, "계란": 155, "닭고기": 165, "소고기": 250, "돼지고기": 242,
    "생선": 120, "두부": 76, "김치": 15, "비빔밥": 490, "불고기": 220,
    "떡볶이": 380, "삼겹살": 330, "라면": 450, "치킨": 300, "김밥": 200,
    "피자": 270, "햄버거": 295, "샐러드": 50, "케이크": 350,
}


class KoreanFoodAnalyzer:
    """한국 음식 특화 이미지 분석기."""

    def __init__(self):
        # ── YOLO ──
        self._recognizer = None
        try:
            from backend.multimodal.food_recognizer import FoodRecognizer
            self._recognizer = FoodRecognizer()
            logger.info("FoodRecognizer(YOLO) 로드 성공")
        except Exception as e:
            logger.warning("YOLO 로드 실패: %s", e)

        # ── CLIP ──
        self._clip = None
        try:
            from backend.multimodal.clip_embedder import CLIPEmbedder
            self._clip = CLIPEmbedder()
            logger.info("CLIPEmbedder 로드 성공")
        except Exception as e:
            logger.warning("CLIP 로드 실패: %s", e)

    def analyze(self, image_bytes: bytes) -> dict[str, Any]:
        """이미지 → 식재료 인식 + 영양정보 추정.

        Args:
            image_bytes: jpeg/png/webp 이미지 바이트

        Returns:
            {detected_items, confidence, nutrition_estimate}
        """
        # 입력 검증
        if len(image_bytes) > 10 * 1024 * 1024:
            return {"error": "이미지 크기 초과 (10MB 제한)", "detected_items": []}

        try:
            from PIL import Image
            img = Image.open(io.BytesIO(image_bytes))
            if img.format and img.format.upper() not in ("JPEG", "PNG", "WEBP"):
                return {"error": f"지원하지 않는 형식: {img.format}", "detected_items": []}
        except Exception:
            return {"error": "이미지 읽기 실패", "detected_items": []}

        # 1단계: YOLO 감지
        detections = self._detect_with_yolo(image_bytes)

        # 2단계: CLIP 보조 분류 (YOLO 결과 없을 때)
        if not detections and self._clip:
            detections = self._classify_with_clip(image_bytes)

        # 3단계: 한국어 이름 매핑 + 영양정보
        detected_items = []
        total_nutrition = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}

        for det in detections:
            label = det.get("label", "unknown")
            korean_name = _KOREAN_NAMES.get(label, label)
            calories = _APPROX_CALORIES.get(korean_name, 100)

            item = {
                "english_name": label,
                "korean_name": korean_name,
                "confidence": det.get("confidence", 0.5),
                "calories_per_100g": calories,
            }
            detected_items.append(item)
            total_nutrition["calories"] += calories

        avg_confidence = (
            sum(d["confidence"] for d in detected_items) / len(detected_items)
            if detected_items else 0
        )

        return {
            "detected_items": detected_items,
            "confidence": round(avg_confidence, 3),
            "nutrition_estimate": total_nutrition,
            "total_items": len(detected_items),
        }

    def _detect_with_yolo(self, image_bytes: bytes) -> list[dict]:
        """YOLO 객체 감지."""
        if self._recognizer is None:
            return []
        try:
            return self._recognizer.detect(image_bytes)
        except Exception as e:
            logger.warning("YOLO 감지 실패: %s", e)
            return []

    def _classify_with_clip(self, image_bytes: bytes) -> list[dict]:
        """CLIP 유사도 기반 분류 (YOLO 폴백).

        TODO(팀원E): Top-K 유사도 검색 + 임계값 튜닝
        """
        if self._clip is None:
            return []
        try:
            import numpy as np
            image_emb = self._clip.embed_image(image_bytes)
            if np.allclose(image_emb, 0):
                return []

            # 한국 음식 카테고리와 유사도 비교
            candidates = ["밥", "김치", "국", "반찬", "고기", "생선", "채소", "과일", "빵", "면"]
            best_label, best_score = "", 0.0
            for candidate in candidates:
                text_emb = self._clip.embed_text(candidate)
                sim = self._clip.compute_similarity(image_emb, text_emb)
                if sim > best_score:
                    best_score = sim
                    best_label = candidate

            if best_score > 0.2:
                return [{"label": best_label, "confidence": float(best_score)}]
        except Exception as e:
            logger.warning("CLIP 분류 실패: %s", e)
        return []


def register(registry):
    """플러그인 등록."""
    try:
        analyzer = KoreanFoodAnalyzer()
        registry.register("image_analyzer", analyzer)
        logger.info("vision_korean 플러그인 활성화")
    except Exception as e:
        logger.warning("vision_korean 플러그인 로드 실패: %s", e)
