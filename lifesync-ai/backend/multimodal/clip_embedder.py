"""OpenCLIP 임베더 — 이미지/텍스트를 512차원 벡터로 임베딩."""

import io
import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class CLIPEmbedder:
    """OpenCLIP 기반 512차원 임베딩 생성기.

    모델은 lazy loading으로 최초 호출 시에만 로드한다.
    """

    def __init__(self, model_name: str = "ViT-B-32") -> None:
        self.model_name = model_name
        self._model: Any = None
        self._preprocess: Any = None
        self._tokenizer: Any = None
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """모델을 lazy load."""
        if self._loaded:
            return

        try:
            import open_clip
            import torch

            self._model, _, self._preprocess = open_clip.create_model_and_transforms(
                self.model_name, pretrained="laion2b_s34b_b79k"
            )
            self._tokenizer = open_clip.get_tokenizer(self.model_name)
            self._model.eval()
            self._loaded = True
            logger.info("OpenCLIP 모델 로드 완료: %s", self.model_name)
        except ImportError:
            logger.warning("open_clip 패키지 미설치")
        except Exception:
            logger.exception("OpenCLIP 모델 로드 실패")

    def embed_image(self, image_bytes: bytes) -> np.ndarray:
        """이미지를 512차원 벡터로 임베딩.

        Args:
            image_bytes: 이미지 바이트 데이터.

        Returns:
            512차원 numpy 배열. 실패 시 영벡터 반환.
        """
        self._ensure_loaded()
        if not self._loaded:
            return np.zeros(512, dtype=np.float32)

        try:
            import torch
            from PIL import Image

            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            image_input = self._preprocess(image).unsqueeze(0)

            with torch.no_grad():
                features = self._model.encode_image(image_input)
                features = features / features.norm(dim=-1, keepdim=True)

            return features.squeeze().cpu().numpy()
        except Exception:
            logger.exception("이미지 임베딩 실패")
            return np.zeros(512, dtype=np.float32)

    def embed_text(self, text: str) -> np.ndarray:
        """텍스트를 512차원 벡터로 임베딩.

        Args:
            text: 임베딩할 텍스트.

        Returns:
            512차원 numpy 배열. 실패 시 영벡터 반환.
        """
        self._ensure_loaded()
        if not self._loaded:
            return np.zeros(512, dtype=np.float32)

        try:
            import torch

            text_input = self._tokenizer([text])

            with torch.no_grad():
                features = self._model.encode_text(text_input)
                features = features / features.norm(dim=-1, keepdim=True)

            return features.squeeze().cpu().numpy()
        except Exception:
            logger.exception("텍스트 임베딩 실패")
            return np.zeros(512, dtype=np.float32)

    def compute_similarity(
        self, image_embedding: np.ndarray, text_embedding: np.ndarray
    ) -> float:
        """이미지-텍스트 유사도 계산 (코사인 유사도).

        Args:
            image_embedding: 이미지 임베딩 벡터.
            text_embedding: 텍스트 임베딩 벡터.

        Returns:
            코사인 유사도 (-1.0 ~ 1.0).
        """
        norm_img = np.linalg.norm(image_embedding)
        norm_txt = np.linalg.norm(text_embedding)

        if norm_img == 0 or norm_txt == 0:
            return 0.0

        return float(np.dot(image_embedding, text_embedding) / (norm_img * norm_txt))
