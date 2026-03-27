"""모델 레지스트리 — S3 저장 + DB 버전 관리 + 자동 동기화.

로컬 GPU에서 학습한 모델을 S3에 업로드하고,
Railway/클라이언트에서 최신 모델을 다운로드하여 사용한다.
"""

import hashlib
import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")
os.makedirs(MODELS_DIR, exist_ok=True)


class ModelRegistry:
    """모델 버전 관리 및 S3 동기화.

    - 모델 업로드: 로컬 → S3 + 버전 메타데이터 저장
    - 모델 다운로드: S3 → 로컬 (최신 버전 자동 선택)
    - 클라이언트 동기화: 버전 체크 API로 최신 여부 확인
    """

    def __init__(self) -> None:
        self._s3_client: Any = None
        self._bucket = os.getenv("S3_BUCKET_NAME", "lifesync-models")
        self._versions: dict[str, dict[str, Any]] = {}
        self._init_s3()
        self._load_local_versions()

    def _init_s3(self) -> None:
        """S3 클라이언트 초기화."""
        try:
            import boto3
            self._s3_client = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            )
            logger.info("S3 클라이언트 초기화 완료: bucket=%s", self._bucket)
        except Exception:
            logger.warning("S3 클라이언트 초기화 실패 (로컬 전용 모드)")

    def _load_local_versions(self) -> None:
        """로컬 버전 메타데이터 로드."""
        meta_path = os.path.join(MODELS_DIR, "versions.json")
        if os.path.exists(meta_path):
            with open(meta_path, encoding="utf-8") as f:
                self._versions = json.load(f)

    def _save_local_versions(self) -> None:
        """로컬 버전 메타데이터 저장."""
        meta_path = os.path.join(MODELS_DIR, "versions.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(self._versions, f, indent=2, ensure_ascii=False)

    def upload_model(
        self,
        model_name: str,
        local_path: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """모델을 S3에 업로드하고 버전 등록.

        Args:
            model_name: 모델 이름 (예: "ppo_policy", "optuna_best").
            local_path: 로컬 모델 파일 경로.
            metadata: 추가 메타데이터 (하이퍼파라미터 등).

        Returns:
            업로드 결과 (version, s3_key, checksum 등).
        """
        if not os.path.exists(local_path):
            return {"status": "error", "detail": f"파일 없음: {local_path}"}

        # 체크섬 계산
        checksum = self._file_checksum(local_path)
        version = int(time.time())
        s3_key = f"models/{model_name}/v{version}/{os.path.basename(local_path)}"

        # S3 업로드
        if self._s3_client:
            try:
                self._s3_client.upload_file(local_path, self._bucket, s3_key)
                logger.info("S3 업로드 완료: %s → %s", local_path, s3_key)
            except Exception:
                logger.exception("S3 업로드 실패")
                return {"status": "error", "detail": "S3 업로드 실패"}
        else:
            logger.info("S3 미설정 — 로컬 버전만 등록: %s", local_path)

        # 버전 메타데이터 등록
        version_info = {
            "version": version,
            "s3_key": s3_key,
            "checksum": checksum,
            "file_size": os.path.getsize(local_path),
            "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "local_path": local_path,
            "metadata": metadata or {},
        }
        self._versions[model_name] = version_info
        self._save_local_versions()

        return {"status": "uploaded", **version_info}

    def download_model(self, model_name: str) -> str | None:
        """S3에서 최신 모델 다운로드.

        Args:
            model_name: 모델 이름.

        Returns:
            로컬 파일 경로. 실패 시 None.
        """
        version_info = self._versions.get(model_name)
        if not version_info:
            logger.warning("모델 버전 정보 없음: %s", model_name)
            return None

        local_path = version_info.get("local_path", "")
        if local_path and os.path.exists(local_path):
            return local_path

        s3_key = version_info.get("s3_key", "")
        if not s3_key or not self._s3_client:
            return None

        download_path = os.path.join(
            MODELS_DIR, model_name, os.path.basename(s3_key)
        )
        os.makedirs(os.path.dirname(download_path), exist_ok=True)

        try:
            self._s3_client.download_file(self._bucket, s3_key, download_path)
            version_info["local_path"] = download_path
            self._save_local_versions()
            logger.info("S3 다운로드 완료: %s → %s", s3_key, download_path)
            return download_path
        except Exception:
            logger.exception("S3 다운로드 실패")
            return None

    def get_latest_version(self, model_name: str) -> dict[str, Any]:
        """최신 모델 버전 정보 조회 (클라이언트 동기화용).

        Args:
            model_name: 모델 이름.

        Returns:
            버전 정보 (version, checksum, file_size, download_url).
        """
        info = self._versions.get(model_name)
        if not info:
            return {"model_name": model_name, "version": 0, "available": False}

        return {
            "model_name": model_name,
            "version": info["version"],
            "checksum": info["checksum"],
            "file_size": info["file_size"],
            "available": True,
            "metadata": info.get("metadata", {}),
        }

    def list_models(self) -> dict[str, Any]:
        """등록된 모든 모델 목록."""
        return {
            name: {
                "version": info["version"],
                "checksum": info["checksum"],
                "uploaded_at": info.get("uploaded_at", ""),
            }
            for name, info in self._versions.items()
        }

    @staticmethod
    def _file_checksum(path: str) -> str:
        """파일 SHA256 체크섬."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
