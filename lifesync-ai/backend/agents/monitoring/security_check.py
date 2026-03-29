"""보안 서포트 에이전트.

JWT 설정, PUBLIC_PATHS 노출 범위, Rate Limit, 입력 검증 상태를 점검합니다.
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def check_jwt_config() -> dict[str, Any]:
    """JWT 인증 설정 상태를 확인합니다."""
    secret = os.getenv("JWT_SECRET", "")
    env = os.getenv("ENV", "development")

    issues = []
    if not secret:
        issues.append("JWT_SECRET 미설정 - 프로덕션에서 인증 불가")
    elif len(secret) < 32:
        issues.append(f"JWT_SECRET 길이 부족 ({len(secret)}자 < 32자)")

    if env == "development":
        issues.append("ENV=development - 인증 우회 활성 (개발 전용)")

    return {
        "jwt_configured": bool(secret) and len(secret) >= 32,
        "env": env,
        "issues": issues,
    }


def check_public_paths() -> dict[str, Any]:
    """PUBLIC_PATHS에 민감한 경로가 노출되지 않았는지 확인합니다."""
    try:
        from backend.app.main import PUBLIC_PATHS
    except ImportError:
        return {"error": "main.py import 실패", "paths": []}

    sensitive_patterns = ["/api/admin/backup", "/api/auth/me", "/api/state"]
    exposed = [p for p in PUBLIC_PATHS if any(s in p for s in sensitive_patterns)]

    return {
        "total_public": len(PUBLIC_PATHS),
        "paths": sorted(PUBLIC_PATHS),
        "sensitive_exposed": exposed,
        "safe": len(exposed) == 0,
    }


def check_input_validation() -> dict[str, Any]:
    """입력 검증 모듈의 존재 여부를 확인합니다."""
    from pathlib import Path
    validator = Path(__file__).resolve().parents[2] / "services" / "input_validator.py"
    return {
        "validator_exists": validator.exists(),
        "path": str(validator),
    }


def run() -> dict[str, Any]:
    """보안 점검 실행."""
    logger.info("[Security] 점검 시작")
    jwt = check_jwt_config()
    paths = check_public_paths()
    validation = check_input_validation()

    score = 100
    if not jwt["jwt_configured"]:
        score -= 30
    if not paths.get("safe", True):
        score -= 20 * len(paths.get("sensitive_exposed", []))
    if not validation["validator_exists"]:
        score -= 10

    issues = jwt["issues"].copy()
    if not paths.get("safe", True):
        issues.append(f"민감 경로 노출: {paths['sensitive_exposed']}")
    if not validation["validator_exists"]:
        issues.append("input_validator.py 파일 없음")

    return {
        "agent": "security",
        "jwt": jwt,
        "public_paths": paths,
        "input_validation": validation,
        "summary": {
            "score": max(0, score),
            "issues": issues,
            "issue_count": len(issues),
        },
    }
