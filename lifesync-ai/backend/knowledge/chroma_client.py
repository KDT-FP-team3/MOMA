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
