"""GPU/CPU 자동 감지 모듈.

각 팀원의 로컬 PC에서 CUDA GPU가 있으면 자동으로 활용하고,
없으면 CPU로 폴백합니다.

사용법:
    from backend.core.device import get_device, get_device_info

    # PyTorch 모델에 디바이스 지정
    device = get_device()          # "cuda" 또는 "cpu"
    model = model.to(device)

    # 디바이스 정보 조회
    info = get_device_info()
    # {"device": "cuda", "gpu_name": "NVIDIA RTX 3060", "vram_gb": 12.0, ...}

환경변수:
    FORCE_CPU=1  → GPU가 있어도 CPU 강제 사용 (디버깅용)
"""

import logging
import os
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_device() -> str:
    """GPU/CPU 자동 감지. CUDA 사용 가능하면 "cuda", 아니면 "cpu".

    환경변수 FORCE_CPU=1 이면 GPU가 있어도 CPU 사용.
    결과는 캐싱되어 한 번만 감지합니다.

    Returns:
        "cuda" 또는 "cpu"
    """
    # 환경변수로 CPU 강제
    if os.getenv("FORCE_CPU", "").strip() == "1":
        logger.info("FORCE_CPU=1 → CPU 강제 사용")
        return "cpu"

    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_mem / (1024 ** 3)
            logger.info("CUDA GPU 감지: %s (VRAM %.1fGB)", gpu_name, vram)
            return "cuda"
        else:
            logger.info("CUDA 미지원 → CPU 사용")
            return "cpu"
    except ImportError:
        logger.info("PyTorch 미설치 → CPU 사용")
        return "cpu"
    except Exception as e:
        logger.warning("GPU 감지 실패: %s → CPU 사용", e)
        return "cpu"


@lru_cache(maxsize=1)
def get_device_info() -> dict[str, Any]:
    """디바이스 상세 정보 조회.

    Returns:
        {device, gpu_name, gpu_count, vram_gb, cuda_version, torch_version}
    """
    device = get_device()
    info: dict[str, Any] = {"device": device}

    try:
        import torch
        info["torch_version"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()

        if device == "cuda":
            info["gpu_name"] = torch.cuda.get_device_name(0)
            info["gpu_count"] = torch.cuda.device_count()
            props = torch.cuda.get_device_properties(0)
            info["vram_gb"] = round(props.total_mem / (1024 ** 3), 1)
            info["cuda_version"] = torch.version.cuda or "unknown"
        else:
            info["gpu_name"] = None
            info["gpu_count"] = 0
            info["vram_gb"] = 0
            info["cuda_version"] = None
    except ImportError:
        info["torch_version"] = None
        info["cuda_available"] = False
        info["gpu_name"] = None
        info["gpu_count"] = 0
        info["vram_gb"] = 0
        info["cuda_version"] = None

    return info


def to_device(tensor_or_model, device: str | None = None):
    """텐서/모델을 지정 디바이스로 이동. 기본값은 자동 감지.

    Args:
        tensor_or_model: PyTorch tensor 또는 nn.Module
        device: "cuda" 또는 "cpu" (None이면 자동 감지)

    Returns:
        이동된 텐서/모델
    """
    target = device or get_device()
    try:
        return tensor_or_model.to(target)
    except Exception as e:
        logger.warning("디바이스 이동 실패 (%s): %s → CPU 폴백", target, e)
        return tensor_or_model.to("cpu")
