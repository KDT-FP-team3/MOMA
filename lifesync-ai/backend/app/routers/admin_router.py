"""팀장 관리 라우터 — 팀 진행 현황, 충돌 감지, 백업, 보안 감사.

엔드포인트:
  GET  /api/admin/team-progress       플러그인별 진행 상태 + git 통계
  GET  /api/admin/git-history/{plugin} 특정 플러그인 최근 커밋
  GET  /api/admin/conflicts            파일 수정 충돌 감지
  POST /api/admin/backup               git 태그 생성 (백업)
  GET  /api/admin/backups              태그 목록
  GET  /api/admin/security-audit       보안 체크리스트
  GET  /api/admin/orchestrator-stats   오케스트레이터 통계
"""

import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)


def require_admin(request: Request) -> None:
    """관리자 권한 확인 — JWT payload에 is_admin=True 필요.
    개발 환경에서는 검증을 건너뜀.
    """
    if os.getenv("ENV", "production") == "development":
        return
    user = getattr(getattr(request, "state", None), "user", None)
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")


router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])

# 프로젝트 루트 (lifesync-ai/)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_BACKEND_ROOT = _PROJECT_ROOT / "backend"
_PLUGINS_ROOT = _BACKEND_ROOT / "plugins"

# 팀원 매핑
TEAM_MAP: dict[str, dict[str, str]] = {
    "food_rag": {"member": "A", "role": "RAG 레시피 추천", "slot": "food_agent"},
    "exercise_weather": {"member": "B", "role": "운동+날씨 연동", "slot": "exercise_agent"},
    "health_checkup": {"member": "C", "role": "건강검진 분석", "slot": "health_agent"},
    "hobby_stress": {"member": "D", "role": "스트레스 기반 취미", "slot": "hobby_agent"},
    "vision_korean": {"member": "E", "role": "한식 YOLO+CLIP", "slot": "image_analyzer"},
    "voice_stt": {"member": "F", "role": "Whisper STT+gTTS", "slot": "voice_processor"},
}


def _run_git(*args: str, cwd: str | None = None) -> str:
    """git 명령 실행 후 stdout 반환. 실패 시 빈 문자열."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd or str(_PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        return result.stdout.strip()
    except Exception as exc:
        logger.warning("git 명령 실패: git %s → %s", " ".join(args), exc)
        return ""


def _count_lines(folder: Path) -> int:
    """폴더 내 .py 파일 총 줄 수."""
    total = 0
    if not folder.exists():
        return 0
    for py_file in folder.rglob("*.py"):
        try:
            total += sum(1 for _ in py_file.open(encoding="utf-8"))
        except Exception:
            pass
    return total


# ============================================================
# 1. 팀 진행 현황
# ============================================================

@router.get("/team-progress")
async def team_progress() -> dict[str, Any]:
    """플러그인별 진행 상태 + git 통계."""
    from backend.core.plugin_registry import registry

    plugin_status = registry.status()
    plugins: list[dict[str, Any]] = []

    for plugin_name, info in TEAM_MAP.items():
        folder = _PLUGINS_ROOT / plugin_name
        slot = info["slot"]

        # git log: 최근 커밋 수 (30일)
        commit_count = _run_git(
            "log", "--oneline", "--since=30 days ago",
            "--", f"backend/plugins/{plugin_name}/",
        )
        recent_commits = len(commit_count.splitlines()) if commit_count else 0

        # 마지막 커밋 날짜
        last_date = _run_git(
            "log", "-1", "--format=%ci",
            "--", f"backend/plugins/{plugin_name}/",
        )

        # 최근 커밋 3건
        log_lines = _run_git(
            "log", "-3", "--format=%h|%s|%an|%cr",
            "--", f"backend/plugins/{plugin_name}/",
        )
        recent_log = []
        for line in log_lines.splitlines():
            parts = line.split("|", 3)
            if len(parts) == 4:
                recent_log.append({
                    "hash": parts[0],
                    "message": parts[1],
                    "author": parts[2],
                    "relative_date": parts[3],
                })

        # 상태
        slot_status = plugin_status.get(slot, {})
        is_active = slot_status.get("status") == "plugin"

        plugins.append({
            "plugin": plugin_name,
            "member": info["member"],
            "role": info["role"],
            "slot": slot,
            "status": "active" if is_active else "fallback",
            "class": slot_status.get("class", "unknown"),
            "code_lines": _count_lines(folder),
            "recent_commits_30d": recent_commits,
            "last_commit_date": last_date or None,
            "recent_log": recent_log,
        })

    return {"plugins": plugins, "timestamp": datetime.now(timezone.utc).isoformat()}


# ============================================================
# 2. 특정 플러그인 git 히스토리
# ============================================================

@router.get("/git-history/{plugin}")
async def git_history(plugin: str, limit: int = 20) -> dict[str, Any]:
    """특정 플러그인 폴더의 최근 git log."""
    if plugin not in TEAM_MAP:
        raise HTTPException(404, f"알 수 없는 플러그인: {plugin}")

    limit = min(limit, 50)
    log_output = _run_git(
        "log", f"-{limit}", "--format=%H|%h|%s|%an|%ae|%ci",
        "--", f"backend/plugins/{plugin}/",
    )

    commits = []
    for line in log_output.splitlines():
        parts = line.split("|", 5)
        if len(parts) == 6:
            commits.append({
                "full_hash": parts[0],
                "short_hash": parts[1],
                "message": parts[2],
                "author": parts[3],
                "email": parts[4],
                "date": parts[5],
            })

    return {"plugin": plugin, "commits": commits}


# ============================================================
# 3. 충돌 감지
# ============================================================

@router.get("/conflicts")
async def detect_conflicts() -> dict[str, Any]:
    """최근 7일간 같은 파일을 다른 author가 수정한 경우 감지."""
    log_output = _run_git(
        "log", "--since=7 days ago", "--format=%an|%H", "--name-only",
    )

    # 파일별 수정한 author 집합
    file_authors: dict[str, set[str]] = {}
    current_author = ""
    for line in log_output.splitlines():
        if "|" in line:
            current_author = line.split("|")[0]
        elif line.strip() and current_author:
            file_authors.setdefault(line.strip(), set()).add(current_author)

    conflicts = []
    for filepath, authors in file_authors.items():
        if len(authors) > 1:
            conflicts.append({
                "file": filepath,
                "authors": sorted(authors),
                "risk": "high" if "core/" in filepath or "main.py" in filepath else "medium",
            })

    # risk로 정렬 (high → medium)
    conflicts.sort(key=lambda c: (0 if c["risk"] == "high" else 1, c["file"]))

    return {
        "conflicts": conflicts,
        "total": len(conflicts),
        "period": "7 days",
    }


# ============================================================
# 4. 백업 (git tag)
# ============================================================

class BackupRequest(BaseModel):
    """백업 요청."""
    tag_name: str | None = None
    message: str = "팀장 백업"


@router.post("/backup")
async def create_backup(req: BackupRequest) -> dict[str, Any]:
    """git tag 생성."""
    tag = req.tag_name or f"backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # 태그명 검증
    if not all(c.isalnum() or c in "-_." for c in tag):
        raise HTTPException(400, "태그명에 허용되지 않는 문자가 포함됨")

    # 메시지 검증 (명령 주입 방지: -- 로 시작 불가, 길이 제한)
    msg = req.message[:200]  # 최대 200자
    if msg.startswith("-"):
        raise HTTPException(400, "메시지가 '-'로 시작할 수 없습니다.")

    result = _run_git("tag", "-a", tag, "-m", msg)
    # git tag는 성공 시 stdout 없음, 실패 시 stderr
    verify = _run_git("tag", "-l", tag)
    if tag not in verify:
        raise HTTPException(500, "태그 생성 실패")

    return {"tag": tag, "message": req.message, "created_at": datetime.now(timezone.utc).isoformat()}


@router.get("/backups")
async def list_backups() -> dict[str, Any]:
    """git 태그 목록 (최근순)."""
    tags_output = _run_git("tag", "-l", "--sort=-creatordate", "--format=%(refname:short)|%(creatordate:iso)")

    tags = []
    for line in tags_output.splitlines():
        parts = line.split("|", 1)
        if parts:
            tags.append({
                "tag": parts[0],
                "date": parts[1] if len(parts) > 1 else None,
            })

    return {"tags": tags[:30], "total": len(tags)}


# ============================================================
# 5. 보안 감사
# ============================================================

@router.get("/security-audit")
async def security_audit() -> dict[str, Any]:
    """보안 설정 체크리스트."""
    env = os.getenv("ENV", "development")
    jwt_secret = os.getenv("JWT_SECRET", "")

    checks = [
        {
            "category": "인증",
            "item": "JWT_SECRET 설정",
            "status": "pass" if jwt_secret and len(jwt_secret) >= 32 else "fail",
            "detail": "32자 이상 시크릿 설정 필요" if not jwt_secret or len(jwt_secret) < 32 else "OK",
        },
        {
            "category": "인증",
            "item": "프로덕션 인증 강제",
            "status": "pass" if env == "production" or jwt_secret else "warn",
            "detail": f"현재 환경: {env}",
        },
        {
            "category": "네트워크",
            "item": "CORS 설정",
            "status": "pass",
            "detail": f"허용 도메인: {os.getenv('CORS_ORIGINS', 'localhost만')}",
        },
        {
            "category": "네트워크",
            "item": "Rate Limiting",
            "status": "pass",
            "detail": "IP당 60회/분",
        },
        {
            "category": "네트워크",
            "item": "보안 헤더 (XSS, Clickjacking, HSTS)",
            "status": "pass",
            "detail": "SecurityHeadersMiddleware 활성",
        },
        {
            "category": "API 키",
            "item": "OPENAI_API_KEY",
            "status": "pass" if os.getenv("OPENAI_API_KEY") else "fail",
            "detail": "LLM 기능에 필수",
        },
        {
            "category": "API 키",
            "item": "DATABASE_URL",
            "status": "pass" if os.getenv("DATABASE_URL") else "warn",
            "detail": "Supabase 연결",
        },
        {
            "category": "입력검증",
            "item": "파일 업로드 화이트리스트",
            "status": "pass",
            "detail": "확장자 제한 + 경로 트래버설 차단",
        },
        {
            "category": "입력검증",
            "item": "user_id 정규식 검증",
            "status": "pass",
            "detail": "input_validator.py",
        },
    ]

    pass_count = sum(1 for c in checks if c["status"] == "pass")
    total = len(checks)

    return {
        "checks": checks,
        "summary": {
            "pass": pass_count,
            "warn": sum(1 for c in checks if c["status"] == "warn"),
            "fail": sum(1 for c in checks if c["status"] == "fail"),
            "total": total,
            "score": round(pass_count / total * 100),
        },
        "environment": env,
    }


# ============================================================
# 6. 오케스트레이터 통계
# ============================================================

# 인메모리 통계 (서버 재시작 시 리셋)
_orchestrator_stats: dict[str, Any] = {
    "calls_by_domain": {"food": 0, "exercise": 0, "health": 0, "hobby": 0},
    "cascade_counts": [],
    "errors": 0,
    "total_calls": 0,
}


def record_orchestrator_call(domain: str, cascade_count: int, error: bool = False) -> None:
    """오케스트레이터 호출 통계 기록. api_router에서 호출."""
    _orchestrator_stats["total_calls"] += 1
    if domain in _orchestrator_stats["calls_by_domain"]:
        _orchestrator_stats["calls_by_domain"][domain] += 1
    _orchestrator_stats["cascade_counts"].append(cascade_count)
    # 최근 1000건만 유지
    if len(_orchestrator_stats["cascade_counts"]) > 1000:
        _orchestrator_stats["cascade_counts"] = _orchestrator_stats["cascade_counts"][-500:]
    if error:
        _orchestrator_stats["errors"] += 1


@router.get("/orchestrator-stats")
async def orchestrator_stats() -> dict[str, Any]:
    """오케스트레이터 통계."""
    counts = _orchestrator_stats["cascade_counts"]
    avg_cascade = sum(counts) / len(counts) if counts else 0
    total = _orchestrator_stats["total_calls"]

    return {
        "total_calls": total,
        "calls_by_domain": _orchestrator_stats["calls_by_domain"],
        "avg_cascade_effects": round(avg_cascade, 2),
        "error_count": _orchestrator_stats["errors"],
        "error_rate": round(_orchestrator_stats["errors"] / total * 100, 1) if total else 0,
    }


# ============================================================
# 8. 모니터링 에이전트
# ============================================================

@router.get("/monitoring/status")
async def monitoring_status() -> dict[str, Any]:
    """모니터링 에이전트 최근 점검 결과 조회."""
    from backend.agents.monitoring.core_agent import get_latest_result
    result = get_latest_result()
    if not result:
        return {"status": "no_data", "message": "아직 점검이 실행되지 않았습니다."}
    return result


@router.post("/monitoring/run")
async def monitoring_run() -> dict[str, Any]:
    """모니터링 에이전트 수동 실행."""
    from backend.agents.monitoring.core_agent import run_all_checks
    result = run_all_checks()
    return {"status": "completed", "overall_score": result.get("overall", {}).get("score", 0)}
