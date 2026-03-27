"""음식 위험도 스코어러 — Bayesian 기반 음식 위험도 평가."""

from typing import Any


# 조리법별 기본 위험도
COOKING_METHOD_RISK: dict[str, float] = {
    "fried": 0.7,
    "deep_fried": 0.8,
    "튀김": 0.8,
    "grilled": 0.3,
    "구이": 0.3,
    "boiled": 0.1,
    "삶음": 0.1,
    "steamed": 0.1,
    "찜": 0.1,
    "raw": 0.15,
    "에어프라이어": 0.15,
    "airfryer": 0.15,
    "볶음": 0.4,
    "조림": 0.25,
}

# 음식 카테고리별 기본 위험도
CATEGORY_RISK: dict[str, float] = {
    "한식-찌개": 0.3,
    "한식-탕": 0.25,
    "한식-구이": 0.35,
    "한식-볶음": 0.4,
    "한식-전": 0.45,
    "한식-면": 0.35,
    "한식-밥": 0.2,
    "한식-분식": 0.4,
    "한식-국": 0.15,
    "한식-반찬": 0.2,
    "양식-면": 0.4,
    "양식-구이": 0.35,
    "양식-샐러드": 0.1,
    "일식-튀김": 0.7,
    "중식-면": 0.45,
    "중식-튀김": 0.7,
    "다이어트-밥": 0.1,
    "다이어트-샐러드": 0.05,
    "다이어트-간식": 0.1,
    "다이어트-구이": 0.1,
}


class FoodRiskScorer:
    """Bayesian 기반 음식 위험도 계산기."""

    def score(self, food_item: str, user_health: dict[str, Any]) -> float:
        """음식 항목의 위험도 점수 계산 (0.0 ~ 1.0).

        Args:
            food_item: 음식 이름 또는 카테고리.
            user_health: 사용자 건강 정보.

        Returns:
            위험도 점수 (0.0 = 안전, 1.0 = 매우 위험).
        """
        base_risk = 0.3

        # 카테고리 기반 위험도
        for category, risk in CATEGORY_RISK.items():
            if category in food_item:
                base_risk = risk
                break

        # 건강 상태에 따른 위험도 조정
        cholesterol = user_health.get("total_cholesterol", 180)
        if cholesterol > 200:
            base_risk *= 1.3  # 고콜레스테롤이면 기름진 음식 위험 증가

        blood_sugar = user_health.get("blood_sugar_fasting", 90)
        if blood_sugar > 100:
            base_risk *= 1.2  # 혈당이 높으면 탄수화물 위험 증가

        bmi = user_health.get("bmi", 22)
        if bmi > 25:
            base_risk *= 1.15  # 과체중이면 전체 위험 증가

        return min(1.0, base_risk)

    def score_by_cooking_method(
        self, cooking_method: str, user_health: dict[str, Any]
    ) -> float:
        """조리법 기반 위험도 계산.

        Args:
            cooking_method: 조리법.
            user_health: 사용자 건강 정보.

        Returns:
            위험도 점수.
        """
        base_risk = COOKING_METHOD_RISK.get(cooking_method, 0.3)

        cholesterol = user_health.get("total_cholesterol", 180)
        if cholesterol > 200 and cooking_method in ("fried", "deep_fried", "튀김"):
            base_risk = min(1.0, base_risk * 1.5)

        return base_risk

    def get_risk_factors(self, food_item: str) -> list[str]:
        """음식 항목의 위험 요인 목록 반환.

        Args:
            food_item: 음식 이름.

        Returns:
            위험 요인 문자열 리스트.
        """
        factors: list[str] = []
        item_lower = food_item.lower()

        if any(k in item_lower for k in ("튀김", "fried", "치킨", "돈까스")):
            factors.append("고지방/트랜스지방 위험")
            factors.append("콜레스테롤 상승 가능")

        if any(k in item_lower for k in ("라면", "짬뽕", "짜장")):
            factors.append("나트륨 과다")
            factors.append("MSG 포함 가능")

        if any(k in item_lower for k in ("삼겹살", "갈비")):
            factors.append("포화지방 함량 높음")

        if any(k in item_lower for k in ("떡볶이", "빙수", "토스트")):
            factors.append("고탄수화물/당분")

        if not factors:
            factors.append("특별한 위험 요인 없음")

        return factors
