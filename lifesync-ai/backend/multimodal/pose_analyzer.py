"""MediaPipe 자세 분석기 — 운동 자세 감지 및 교정."""

import io
import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class PoseAnalyzer:
    """MediaPipe 기반 자세 분석기.

    모델은 lazy loading으로 최초 호출 시에만 로드한다.
    """

    def __init__(self) -> None:
        self._pose: Any = None
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """MediaPipe Pose lazy load."""
        if self._loaded:
            return

        try:
            import mediapipe as mp
            self._pose = mp.solutions.pose.Pose(
                static_image_mode=True,
                model_complexity=1,
                min_detection_confidence=0.5,
            )
            self._loaded = True
            logger.info("MediaPipe Pose 모델 로드 완료")
        except ImportError:
            logger.warning("mediapipe 패키지 미설치")
        except Exception:
            logger.exception("MediaPipe 모델 로드 실패")

    def analyze(self, image_bytes: bytes) -> dict[str, Any]:
        """이미지에서 자세 분석.

        Args:
            image_bytes: 이미지 바이트 데이터.

        Returns:
            자세 분석 결과 (landmarks, posture_score 등).
        """
        self._ensure_loaded()
        if not self._loaded:
            return {"landmarks": {}, "posture_score": 0.0, "detected": False}

        try:
            from PIL import Image

            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            image_array = np.array(image)

            results = self._pose.process(image_array)

            if not results.pose_landmarks:
                return {"landmarks": {}, "posture_score": 0.0, "detected": False}

            landmarks: dict[str, dict[str, float]] = {}
            for i, lm in enumerate(results.pose_landmarks.landmark):
                landmarks[f"landmark_{i}"] = {
                    "x": lm.x,
                    "y": lm.y,
                    "z": lm.z,
                    "visibility": lm.visibility,
                }

            posture_score = self._evaluate_posture(landmarks)

            return {
                "landmarks": landmarks,
                "posture_score": posture_score,
                "detected": True,
                "shoulder_alignment": self._check_shoulder_alignment(landmarks),
                "spine_alignment": self._check_spine_alignment(landmarks),
            }
        except Exception:
            logger.exception("자세 분석 실패")
            return {"landmarks": {}, "posture_score": 0.0, "detected": False}

    def evaluate_form(
        self, pose_data: dict[str, Any], exercise: str
    ) -> dict[str, Any]:
        """운동 자세 평가 및 교정 피드백.

        Args:
            pose_data: analyze()의 반환값.
            exercise: 운동 이름.

        Returns:
            자세 평가 결과 (score, corrections, tips).
        """
        if not pose_data.get("detected", False):
            return {
                "score": 0.0,
                "corrections": ["자세를 감지할 수 없습니다. 전신이 보이도록 촬영해주세요."],
                "tips": [],
            }

        corrections: list[str] = []
        tips: list[str] = []
        score = pose_data.get("posture_score", 50.0)

        shoulder = pose_data.get("shoulder_alignment", {})
        if shoulder.get("is_uneven", False):
            corrections.append("어깨 높이가 불균형합니다. 양쪽 어깨를 수평으로 맞추세요.")
            score -= 10

        spine = pose_data.get("spine_alignment", {})
        if spine.get("is_curved", False):
            corrections.append("척추가 휘어져 있습니다. 허리를 곧게 펴주세요.")
            score -= 15

        if exercise in ("스쿼트", "squat"):
            tips.append("무릎이 발끝을 넘지 않도록 주의하세요.")
            tips.append("가슴을 펴고 시선은 정면을 향하세요.")
        elif exercise in ("데드리프트", "deadlift"):
            tips.append("허리를 곧게 유지하세요.")
            tips.append("바벨은 몸에 최대한 가깝게 유지하세요.")
        elif exercise in ("푸시업", "pushup"):
            tips.append("몸을 일직선으로 유지하세요.")
            tips.append("팔꿈치 각도를 45도로 유지하세요.")

        return {
            "score": max(0, min(100, score)),
            "corrections": corrections,
            "tips": tips,
        }

    def _evaluate_posture(self, landmarks: dict[str, dict[str, float]]) -> float:
        """전체 자세 점수 계산."""
        score = 70.0

        shoulder_check = self._check_shoulder_alignment(landmarks)
        if shoulder_check.get("is_uneven", False):
            score -= 10

        spine_check = self._check_spine_alignment(landmarks)
        if spine_check.get("is_curved", False):
            score -= 15

        return max(0, min(100, score))

    def _check_shoulder_alignment(
        self, landmarks: dict[str, dict[str, float]]
    ) -> dict[str, Any]:
        """어깨 정렬 확인."""
        left_shoulder = landmarks.get("landmark_11", {})
        right_shoulder = landmarks.get("landmark_12", {})

        if not left_shoulder or not right_shoulder:
            return {"is_uneven": False, "diff": 0.0}

        y_diff = abs(left_shoulder.get("y", 0) - right_shoulder.get("y", 0))
        return {"is_uneven": y_diff > 0.05, "diff": y_diff}

    def _check_spine_alignment(
        self, landmarks: dict[str, dict[str, float]]
    ) -> dict[str, Any]:
        """척추 정렬 확인."""
        nose = landmarks.get("landmark_0", {})
        mid_hip_left = landmarks.get("landmark_23", {})
        mid_hip_right = landmarks.get("landmark_24", {})

        if not nose or not mid_hip_left or not mid_hip_right:
            return {"is_curved": False, "deviation": 0.0}

        hip_x = (mid_hip_left.get("x", 0) + mid_hip_right.get("x", 0)) / 2
        deviation = abs(nose.get("x", 0) - hip_x)
        return {"is_curved": deviation > 0.1, "deviation": deviation}
