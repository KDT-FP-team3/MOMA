"""운동 DB — ChromaDB 기반 운동 데이터 벡터 검색."""

import json
import logging
import os
from typing import Any

from backend.knowledge.chroma_client import ChromaClient

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


class ExerciseDB:
    """운동 + 부상 데이터 벡터 DB."""

    COLLECTION_NAME = "exercises"

    def __init__(self, chroma_client: ChromaClient | None = None) -> None:
        self._client = chroma_client or ChromaClient()
        self._raw_data: list[dict[str, Any]] = []
        self._ensure_seeded()

    def _ensure_seeded(self) -> None:
        """시드 데이터가 없으면 JSON에서 로드."""
        collection = self._client.get_or_create_collection(self.COLLECTION_NAME)

        json_path = os.path.join(DATA_DIR, "exercises.json")
        if os.path.exists(json_path):
            with open(json_path, encoding="utf-8") as f:
                self._raw_data = json.load(f)

        if collection.count() > 0:
            return

        if not self._raw_data:
            logger.warning("exercises.json 파일이 비어 있음")
            return

        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for ex in self._raw_data:
            doc = (
                f"{ex['name']} - {ex['category']} - "
                f"근육: {', '.join(ex.get('muscle_groups', []))} - "
                f"{ex.get('description', '')}"
            )
            documents.append(doc)
            metadatas.append(
                {
                    "name": ex["name"],
                    "category": ex["category"],
                    "difficulty": ex.get("difficulty", 1),
                    "calories_per_30min": ex.get("calories_per_30min", 0),
                    "indoor": ex.get("indoor", True),
                }
            )

        self._client.add_documents(self.COLLECTION_NAME, documents, metadatas)
        logger.info("운동 데이터 %d건 시딩 완료", len(documents))

    def search(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """운동 데이터 검색.

        Args:
            query: 검색 쿼리 (예: "실내 유산소 운동").
            n_results: 반환할 결과 수.

        Returns:
            유사도 순 운동 리스트.
        """
        return self._client.query(self.COLLECTION_NAME, query, n_results)

    def get_injury_data(self, exercise: str) -> dict[str, Any]:
        """운동별 부상 데이터 조회.

        Args:
            exercise: 운동 이름.

        Returns:
            부상 위험 정보 딕셔너리.
        """
        for ex in self._raw_data:
            if ex["name"] == exercise:
                return {
                    "exercise": exercise,
                    "injury_risks": ex.get("injury_risks", []),
                    "difficulty": ex.get("difficulty", 1),
                }
        return {"exercise": exercise, "injury_risks": [], "difficulty": 1}

    def get_indoor_exercises(self) -> list[dict[str, Any]]:
        """실내 가능 운동 목록 조회."""
        return [ex for ex in self._raw_data if ex.get("indoor", False)]
