"""YOLO 식재료 인식기 — 이미지에서 식재료를 감지하고 분류."""

import io
import logging
from typing import Any

logger = logging.getLogger(__name__)


class FoodRecognizer:
    """YOLO 기반 식재료 인식기.

    모델은 lazy loading으로 최초 호출 시에만 로드한다.
    """

    def __init__(self, model_path: str = "yolov8n.pt") -> None:
        self.model_path = model_path
        self._model: Any = None
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """YOLO 모델 lazy load."""
        if self._loaded:
            return

        try:
            from ultralytics import YOLO
            self._model = YOLO(self.model_path)
            self._loaded = True
            logger.info("YOLO 모델 로드 완료: %s", self.model_path)
        except ImportError:
            logger.warning("ultralytics 패키지 미설치")
        except Exception:
            logger.exception("YOLO 모델 로드 실패")

    def detect(self, image_bytes: bytes) -> list[dict[str, Any]]:
        """이미지에서 객체 감지.

        Args:
            image_bytes: 이미지 바이트 데이터.

        Returns:
            감지 결과 리스트 (label, confidence, bbox).
        """
        self._ensure_loaded()
        if not self._loaded:
            return []

        try:
            from PIL import Image

            image = Image.open(io.BytesIO(image_bytes))
            results = self._model(image, verbose=False)

            detections: list[dict[str, Any]] = []
            for result in results:
                for box in result.boxes:
                    detections.append(
                        {
                            "label": result.names[int(box.cls[0])],
                            "confidence": float(box.conf[0]),
                            "bbox": box.xyxy[0].tolist(),
                        }
                    )

            return detections
        except Exception:
            logger.exception("객체 감지 실패")
            return []

    def classify(self, image_bytes: bytes) -> list[str]:
        """이미지에서 객체 분류 (라벨만 반환).

        Args:
            image_bytes: 이미지 바이트 데이터.

        Returns:
            감지된 객체 라벨 리스트.
        """
        detections = self.detect(image_bytes)
        return [d["label"] for d in detections if d["confidence"] > 0.5]
