"""코드 품질 서포트 에이전트.

플러그인 코드의 인터페이스 준수, 반환값 구조, 필수 메서드 존재를 점검합니다.
"""

import importlib
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_PLUGINS_DIR = Path(__file__).resolve().parents[2] / "plugins"

# 슬롯별 필수 메서드
_REQUIRED_METHODS: dict[str, list[str]] = {
    "food_agent": ["recommend"],
    "exercise_agent": ["recommend"],
    "health_agent": ["recommend", "analyze_checkup"],
    "hobby_agent": ["recommend"],
    "image_analyzer": ["analyze"],
    "voice_processor": ["speech_to_text", "text_to_speech"],
}

# recommend() 반환값 필수 키
_REQUIRED_RETURN_KEYS = {"recommendations", "explanation"}


def check_plugin_interfaces() -> list[dict[str, Any]]:
    """각 플러그인의 인터페이스 준수 여부를 점검합니다.

    Returns:
        플러그인별 점검 결과 리스트.
    """
    results = []
    plugin_folders = [
        ("food_rag", "food_agent"),
        ("exercise_weather", "exercise_agent"),
        ("health_checkup", "health_agent"),
        ("hobby_stress", "hobby_agent"),
        ("vision_korean", "image_analyzer"),
        ("voice_stt", "voice_processor"),
    ]

    for folder, slot in plugin_folders:
        result = {"plugin": folder, "slot": slot, "status": "pass", "issues": []}
        plugin_path = _PLUGINS_DIR / folder / "plugin.py"

        if not plugin_path.exists():
            result["status"] = "skip"
            result["issues"].append("plugin.py 파일 없음")
            results.append(result)
            continue

        # register() 함수 존재 확인
        try:
            mod = importlib.import_module(f"backend.plugins.{folder}.plugin")
            if not hasattr(mod, "register"):
                result["status"] = "fail"
                result["issues"].append("register() 함수 없음")
        except Exception as e:
            result["status"] = "warn"
            result["issues"].append(f"임포트 실패: {type(e).__name__}")

        # 필수 메서드 확인 (소스 코드 분석)
        try:
            source = plugin_path.read_text(encoding="utf-8")
            for method in _REQUIRED_METHODS.get(slot, []):
                if f"def {method}(" not in source:
                    result["status"] = "fail"
                    result["issues"].append(f"{method}() 메서드 미구현")
        except Exception:
            pass

        if not result["issues"]:
            result["issues"].append("모든 인터페이스 준수")

        results.append(result)

    return results


def check_code_lines() -> dict[str, int]:
    """각 플러그인 폴더의 Python 코드 줄 수를 집계합니다."""
    counts = {}
    for folder in _PLUGINS_DIR.iterdir():
        if folder.is_dir() and not folder.name.startswith("_"):
            total = 0
            for py in folder.rglob("*.py"):
                try:
                    total += sum(1 for _ in py.open(encoding="utf-8"))
                except Exception:
                    pass
            counts[folder.name] = total
    return counts


def run() -> dict[str, Any]:
    """코드 품질 점검 실행."""
    logger.info("[CodeQuality] 점검 시작")
    interfaces = check_plugin_interfaces()
    lines = check_code_lines()

    fail_count = sum(1 for r in interfaces if r["status"] == "fail")
    warn_count = sum(1 for r in interfaces if r["status"] == "warn")

    return {
        "agent": "code_quality",
        "interfaces": interfaces,
        "code_lines": lines,
        "summary": {
            "total_plugins": len(interfaces),
            "pass": sum(1 for r in interfaces if r["status"] == "pass"),
            "fail": fail_count,
            "warn": warn_count,
            "score": max(0, 100 - fail_count * 20 - warn_count * 10),
        },
    }
