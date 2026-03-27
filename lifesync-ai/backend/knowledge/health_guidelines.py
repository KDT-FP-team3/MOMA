"""건강검진 가이드라인 DB — ChromaDB 기반 건강 기준치 관리."""

import json
import logging
import os
from typing import Any

from backend.knowledge.chroma_client import ChromaClient

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


class HealthGuidelinesDB:
    """건강검진 가이드라인 벡터 DB."""

    COLLECTION_NAME = "health_guidelines"

    def __init__(self, chroma_client: ChromaClient | None = None) -> None:
        self._client = chroma_client or ChromaClient()
        self._raw_data: list[dict[str, Any]] = []
        self._ensure_seeded()

    def _ensure_seeded(self) -> None:
        """시드 데이터 로드."""
        json_path = os.path.join(DATA_DIR, "health_guidelines.json")
        if os.path.exists(json_path):
            with open(json_path, encoding="utf-8") as f:
                self._raw_data = json.load(f)

        collection = self._client.get_or_create_collection(self.COLLECTION_NAME)
        if collection.count() > 0:
            return

        if not self._raw_data:
            logger.warning("health_guidelines.json 파일이 비어 있음")
            return

        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for guideline in self._raw_data:
            doc = (
                f"{guideline['name']} ({guideline['metric']}) - "
                f"정상 범위: {guideline['normal_min']}~{guideline['normal_max']} {guideline['unit']} - "
                f"주의: {guideline.get('advice_high', '')} - "
                f"부족: {guideline.get('advice_low', '')}"
            )
            documents.append(doc)
            metadatas.append(
                {
                    "metric": guideline["metric"],
                    "name": guideline["name"],
                    "unit": guideline["unit"],
                    "normal_min": float(guideline["normal_min"]),
                    "normal_max": float(guideline["normal_max"]),
                }
            )

        self._client.add_documents(
            self.COLLECTION_NAME, documents, metadatas
        )
        logger.info("건강 가이드라인 %d건 시딩 완료", len(documents))

    def search(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """가이드라인 검색.

        Args:
            query: 검색 쿼리 (예: "콜레스테롤 관리").
            n_results: 반환할 결과 수.

        Returns:
            관련 가이드라인 리스트.
        """
        return self._client.query(self.COLLECTION_NAME, query, n_results)

    def get_reference_range(self, metric: str) -> dict[str, float]:
        """건강 지표 기준 범위 조회.

        Args:
            metric: 지표 키 (예: "blood_pressure_sys").

        Returns:
            기준 범위 딕셔너리 (normal_min, normal_max, warning_max, danger_max).
        """
        for g in self._raw_data:
            if g["metric"] == metric:
                return {
                    "normal_min": float(g["normal_min"]),
                    "normal_max": float(g["normal_max"]),
                    "warning_max": float(g["warning_max"]),
                    "danger_max": float(g["danger_max"]),
                    "unit": g["unit"],
                }
        return {"normal_min": 0, "normal_max": 100, "warning_max": 150, "danger_max": 200, "unit": ""}

    def evaluate_metric(self, metric: str, value: float) -> dict[str, Any]:
        """건강 지표 값 평가.

        Args:
            metric: 지표 키.
            value: 측정 값.

        Returns:
            평가 결과 (status, advice).
        """
        ref = self.get_reference_range(metric)
        guideline = next((g for g in self._raw_data if g["metric"] == metric), {})

        if value < ref["normal_min"]:
            return {"status": "low", "advice": guideline.get("advice_low", "")}
        if value <= ref["normal_max"]:
            return {"status": "normal", "advice": "정상 범위입니다."}
        if value <= ref["warning_max"]:
            return {"status": "warning", "advice": guideline.get("advice_high", "")}
        return {"status": "danger", "advice": guideline.get("advice_high", "")}
