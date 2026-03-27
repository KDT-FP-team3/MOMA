"""레시피 DB — ChromaDB 기반 레시피 벡터 검색."""

import csv
import logging
import os
from typing import Any

from backend.knowledge.chroma_client import ChromaClient

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


class RecipeDB:
    """레시피 벡터 DB.

    ChromaDB에 레시피 데이터를 저장하고 유사도 검색을 제공한다.
    """

    COLLECTION_NAME = "recipes"

    def __init__(self, chroma_client: ChromaClient | None = None) -> None:
        self._client = chroma_client or ChromaClient()
        self._ensure_seeded()

    def _ensure_seeded(self) -> None:
        """시드 데이터가 없으면 CSV에서 로드."""
        collection = self._client.get_or_create_collection(self.COLLECTION_NAME)
        if collection.count() > 0:
            return

        csv_path = os.path.join(DATA_DIR, "recipes.csv")
        if not os.path.exists(csv_path):
            logger.warning("recipes.csv 파일 없음: %s", csv_path)
            return

        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                doc = (
                    f"{row['name']} - {row['category']} - "
                    f"재료: {row['ingredients']} - {row['instructions']}"
                )
                documents.append(doc)
                metadatas.append(
                    {
                        "name": row["name"],
                        "category": row["category"],
                        "calories": float(row.get("calories", 0)),
                        "protein": float(row.get("protein", 0)),
                        "fat": float(row.get("fat", 0)),
                        "carbs": float(row.get("carbs", 0)),
                    }
                )

        if documents:
            self._client.add_documents(
                self.COLLECTION_NAME, documents, metadatas
            )
            logger.info("레시피 %d건 시딩 완료", len(documents))

    def search(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """레시피 검색.

        Args:
            query: 검색 쿼리 (예: "고단백 저칼로리 저녁 메뉴").
            n_results: 반환할 결과 수.

        Returns:
            유사도 순 레시피 리스트.
        """
        return self._client.query(self.COLLECTION_NAME, query, n_results)

    def add_recipe(self, recipe: dict[str, Any]) -> None:
        """레시피 추가.

        Args:
            recipe: 레시피 정보 딕셔너리.
        """
        doc = (
            f"{recipe['name']} - {recipe.get('category', '')} - "
            f"재료: {recipe.get('ingredients', '')} - "
            f"{recipe.get('instructions', '')}"
        )
        metadata = {
            "name": recipe["name"],
            "category": recipe.get("category", ""),
            "calories": float(recipe.get("calories", 0)),
            "protein": float(recipe.get("protein", 0)),
            "fat": float(recipe.get("fat", 0)),
            "carbs": float(recipe.get("carbs", 0)),
        }
        self._client.add_documents(self.COLLECTION_NAME, [doc], [metadata])
