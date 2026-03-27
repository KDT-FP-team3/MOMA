"""취미 카탈로그 DB — ChromaDB 기반 취미 활동 관리."""

import logging
from typing import Any

from backend.knowledge.chroma_client import ChromaClient

logger = logging.getLogger(__name__)

# 기본 취미 카탈로그 (시드 데이터)
DEFAULT_HOBBIES: list[dict[str, Any]] = [
    {"name": "기타 연주", "category": "music", "stress_relief": 0.8, "indoor": True, "description": "기타 연주는 집중력 향상과 스트레스 해소에 효과적입니다. 손가락 운동으로 뇌 활성화에도 도움됩니다."},
    {"name": "피아노", "category": "music", "stress_relief": 0.85, "indoor": True, "description": "피아노 연주는 양손 협응력과 집중력을 키우며 정서적 안정에 기여합니다."},
    {"name": "명상", "category": "mindfulness", "stress_relief": 0.95, "indoor": True, "description": "명상은 스트레스 감소, 불안 해소, 수면 질 향상에 매우 효과적입니다."},
    {"name": "요가", "category": "mindfulness", "stress_relief": 0.9, "indoor": True, "description": "요가는 유연성 향상, 스트레스 해소, 체형 교정에 도움됩니다."},
    {"name": "그림 그리기", "category": "art", "stress_relief": 0.75, "indoor": True, "description": "그림 그리기는 창의력 발휘와 감정 표현을 통한 스트레스 해소에 효과적입니다."},
    {"name": "독서", "category": "intellectual", "stress_relief": 0.7, "indoor": True, "description": "독서는 지식 확장, 집중력 향상, 스트레스 감소에 효과적입니다."},
    {"name": "등산", "category": "outdoor", "stress_relief": 0.85, "indoor": False, "description": "등산은 자연 속 유산소 운동으로 심폐 기능 향상과 스트레스 해소에 탁월합니다."},
    {"name": "사진 촬영", "category": "art", "stress_relief": 0.65, "indoor": False, "description": "사진 촬영은 관찰력과 창의력을 키우며 야외 활동을 촉진합니다."},
    {"name": "요리", "category": "lifestyle", "stress_relief": 0.7, "indoor": True, "description": "요리는 창의적 활동이자 건강한 식습관 형성에 기여합니다."},
    {"name": "보드게임", "category": "social", "stress_relief": 0.6, "indoor": True, "description": "보드게임은 전략적 사고력과 사회성을 기르며 스트레스를 해소합니다."},
    {"name": "정원 가꾸기", "category": "outdoor", "stress_relief": 0.8, "indoor": False, "description": "정원 가꾸기는 자연과 교감하며 마음의 안정을 가져다줍니다."},
    {"name": "뜨개질", "category": "craft", "stress_relief": 0.75, "indoor": True, "description": "뜨개질은 반복적 손동작으로 명상 효과와 성취감을 줍니다."},
    {"name": "캘리그라피", "category": "art", "stress_relief": 0.7, "indoor": True, "description": "캘리그라피는 집중력 향상과 예술적 감성 발달에 효과적입니다."},
    {"name": "자전거", "category": "outdoor", "stress_relief": 0.8, "indoor": False, "description": "자전거 타기는 유산소 운동과 자연 감상을 동시에 즐길 수 있습니다."},
    {"name": "수영", "category": "sports", "stress_relief": 0.85, "indoor": True, "description": "수영은 전신 운동이자 스트레스 해소에 탁월한 취미입니다."},
    {"name": "댄스", "category": "sports", "stress_relief": 0.8, "indoor": True, "description": "댄스는 음악과 함께하는 유산소 운동으로 기분 전환에 효과적입니다."},
    {"name": "퍼즐", "category": "intellectual", "stress_relief": 0.6, "indoor": True, "description": "퍼즐은 두뇌 활성화와 집중력 향상에 도움됩니다."},
    {"name": "블로그 작성", "category": "intellectual", "stress_relief": 0.55, "indoor": True, "description": "블로그 작성은 생각 정리와 자기 표현을 통한 스트레스 관리에 효과적입니다."},
    {"name": "영화 감상", "category": "entertainment", "stress_relief": 0.6, "indoor": True, "description": "영화 감상은 감정적 카타르시스를 통한 스트레스 해소에 효과적입니다."},
    {"name": "반려동물 돌보기", "category": "lifestyle", "stress_relief": 0.9, "indoor": True, "description": "반려동물과의 교감은 옥시토신 분비를 촉진하여 스트레스를 크게 줄여줍니다."},
]


class HobbyCatalogDB:
    """취미 카탈로그 벡터 DB."""

    COLLECTION_NAME = "hobby_catalog"

    def __init__(self, chroma_client: ChromaClient | None = None) -> None:
        self._client = chroma_client or ChromaClient()
        self._raw_data = DEFAULT_HOBBIES.copy()
        self._ensure_seeded()

    def _ensure_seeded(self) -> None:
        """시드 데이터 로드."""
        collection = self._client.get_or_create_collection(self.COLLECTION_NAME)
        if collection.count() > 0:
            return

        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for hobby in self._raw_data:
            documents.append(
                f"{hobby['name']} - {hobby['category']} - {hobby['description']}"
            )
            metadatas.append(
                {
                    "name": hobby["name"],
                    "category": hobby["category"],
                    "stress_relief": hobby["stress_relief"],
                    "indoor": hobby["indoor"],
                }
            )

        self._client.add_documents(self.COLLECTION_NAME, documents, metadatas)
        logger.info("취미 카탈로그 %d건 시딩 완료", len(documents))

    def search(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """취미 검색.

        Args:
            query: 검색 쿼리 (예: "스트레스 해소 실내 활동").
            n_results: 반환할 결과 수.

        Returns:
            관련 취미 리스트.
        """
        return self._client.query(self.COLLECTION_NAME, query, n_results)

    def get_stress_relief_score(self, hobby: str) -> float:
        """취미의 스트레스 해소 점수 조회.

        Args:
            hobby: 취미 이름.

        Returns:
            스트레스 해소 점수 (0.0 ~ 1.0).
        """
        for h in self._raw_data:
            if h["name"] == hobby:
                return h["stress_relief"]
        return 0.5

    def get_by_category(self, category: str) -> list[dict[str, Any]]:
        """카테고리별 취미 조회."""
        return [h for h in self._raw_data if h["category"] == category]
