"""ChromaDB 클라이언트 — 벡터 DB 공통 인터페이스."""

import logging
import os
import uuid
from typing import Any

import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)


class ChromaClient:
    """ChromaDB 공통 클라이언트.

    PersistentClient를 사용하여 로컬에 벡터 데이터를 영속화한다.
    한국어 텍스트를 위해 multilingual 임베딩 함수를 사용한다.
    """

    def __init__(self, persist_dir: str | None = None) -> None:
        self.persist_dir = persist_dir or os.getenv("CHROMA_PATH", "/data/chroma")
        self._client = chromadb.PersistentClient(path=self.persist_dir)
        self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        logger.info("ChromaDB 클라이언트 초기화: path=%s", self.persist_dir)

    def get_or_create_collection(self, name: str) -> chromadb.Collection:
        """컬렉션 조회 또는 생성.

        Args:
            name: 컬렉션 이름.

        Returns:
            ChromaDB Collection 객체.
        """
        return self._client.get_or_create_collection(
            name=name,
            embedding_function=self._embedding_fn,
        )

    def query(
        self, collection_name: str, query_text: str, n_results: int = 5
    ) -> list[dict[str, Any]]:
        """벡터 유사도 검색.

        Args:
            collection_name: 검색 대상 컬렉션 이름.
            query_text: 검색 쿼리 텍스트.
            n_results: 반환할 결과 수.

        Returns:
            유사도 순으로 정렬된 검색 결과 리스트.
        """
        collection = self.get_or_create_collection(collection_name)
        if collection.count() == 0:
            return []

        actual_n = min(n_results, collection.count())
        results = collection.query(
            query_texts=[query_text],
            n_results=actual_n,
        )

        return self._format_results(results)

    def query_expanded(
        self,
        collection_name: str,
        query_text: str,
        context: dict[str, Any] | None = None,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        """쿼리 확장 + 리랭킹 검색.

        원본 쿼리와 컨텍스트 기반 확장 쿼리를 함께 검색한 후,
        거리 기반 리랭킹으로 결과를 통합한다.

        Args:
            collection_name: 컬렉션 이름.
            query_text: 원본 검색 쿼리.
            context: 사용자 상태 컨텍스트 (BMI, 목표, 선호 등).
            n_results: 최종 반환 결과 수.

        Returns:
            리랭킹된 검색 결과 리스트.
        """
        collection = self.get_or_create_collection(collection_name)
        if collection.count() == 0:
            return []

        # 1. 쿼리 확장: 컨텍스트 기반 보조 쿼리 생성
        queries = [query_text]
        if context:
            expanded = self._expand_query(query_text, context)
            queries.extend(expanded)

        # 2. 다중 쿼리 검색 (후보 풀 확대)
        fetch_n = min(n_results * 3, collection.count())
        seen_ids: set[str] = set()
        candidates: list[dict[str, Any]] = []

        for q in queries:
            results = collection.query(query_texts=[q], n_results=fetch_n)
            for item in self._format_results(results):
                if item["id"] not in seen_ids:
                    seen_ids.add(item["id"])
                    candidates.append(item)

        # 3. 리랭킹: 거리 점수 + 컨텍스트 관련성 부스트
        for item in candidates:
            base_score = 1.0 / (1.0 + item["distance"])
            boost = self._context_boost(item, context) if context else 0.0
            item["relevance_score"] = base_score + boost

        candidates.sort(key=lambda x: x["relevance_score"], reverse=True)
        return candidates[:n_results]

    def _expand_query(
        self, query: str, context: dict[str, Any]
    ) -> list[str]:
        """컨텍스트 기반 쿼리 확장."""
        expanded: list[str] = []

        bmi = context.get("bmi", 0)
        if bmi > 25:
            expanded.append(f"{query} 저칼로리 다이어트")
        elif bmi < 18.5:
            expanded.append(f"{query} 고단백 영양")

        stress = context.get("stress_level", 0)
        if stress > 60:
            expanded.append(f"{query} 스트레스 해소")

        goal = context.get("goal", "")
        if goal:
            expanded.append(f"{query} {goal}")

        return expanded[:2]  # 최대 2개 확장 쿼리

    def _context_boost(
        self, item: dict[str, Any], context: dict[str, Any]
    ) -> float:
        """컨텍스트 관련성 부스트 점수 계산."""
        boost = 0.0
        meta = item.get("metadata", {})
        doc = item.get("document", "").lower()

        # 칼로리 목표 관련성
        cal_target = context.get("calorie_target", 0)
        cal_item = meta.get("calories", 0)
        if cal_target > 0 and cal_item > 0:
            diff_ratio = abs(cal_target - cal_item) / cal_target
            if diff_ratio < 0.2:
                boost += 0.15

        # BMI 기반 키워드 부스트
        bmi = context.get("bmi", 0)
        if bmi > 25 and any(kw in doc for kw in ["저칼로리", "샐러드", "닭가슴살"]):
            boost += 0.1
        if bmi < 18.5 and any(kw in doc for kw in ["고단백", "영양", "칼로리"]):
            boost += 0.1

        return boost

    def _format_results(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        """ChromaDB 결과를 표준 형식으로 변환."""
        formatted: list[dict[str, Any]] = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]

        for i, doc in enumerate(documents):
            formatted.append(
                {
                    "id": ids[i] if i < len(ids) else "",
                    "document": doc,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "distance": distances[i] if i < len(distances) else 0.0,
                }
            )

        return formatted

    def add_documents(
        self,
        collection_name: str,
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """문서 추가.

        Args:
            collection_name: 대상 컬렉션 이름.
            documents: 추가할 문서 텍스트 리스트.
            metadatas: 문서별 메타데이터 리스트. None이면 빈 메타데이터 사용.
        """
        collection = self.get_or_create_collection(collection_name)
        ids = [str(uuid.uuid4()) for _ in documents]

        if metadatas is None:
            metadatas = [{} for _ in documents]

        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info(
            "문서 %d건 추가: collection=%s", len(documents), collection_name
        )
