"""CLAUDE.md 자동 업데이트 모듈.

에이전트 점검 결과를 루트 CLAUDE.md와 각 팀원 CLAUDE.md에 반영합니다.
기존 내용은 유지하고, '## 에이전트 점검 현황' 섹션만 교체합니다.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ROOT_CLAUDE_MD = _PROJECT_ROOT / "CLAUDE.md"
_PLUGINS_DIR = _PROJECT_ROOT / "lifesync-ai" / "backend" / "plugins"

# 실제 CLAUDE.md 위치 탐색
if not _ROOT_CLAUDE_MD.exists():
    _alt = _PROJECT_ROOT.parent / "CLAUDE.md"
    if _alt.exists():
        _ROOT_CLAUDE_MD = _alt
    else:
        for candidate in [
            _PROJECT_ROOT / "MOMA" / "CLAUDE.md",
            Path(__file__).resolve().parents[4] / "CLAUDE.md",
        ]:
            if candidate.exists():
                _ROOT_CLAUDE_MD = candidate
                break

# 플러그인 디렉토리 탐색
if not _PLUGINS_DIR.exists():
    _alt_plugins = Path(__file__).resolve().parents[2] / "plugins"
    if _alt_plugins.exists():
        _PLUGINS_DIR = _alt_plugins

_SECTION_MARKER = "## 에이전트 점검 현황 (자동 업데이트)"
_PLUGIN_SECTION_MARKER = "## 에이전트 피드백 (자동)"


def _generate_root_section(results: dict[str, Any]) -> str:
    """루트 CLAUDE.md에 삽입할 에이전트 점검 현황 섹션을 생성합니다."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    code_q = results.get("code_quality", {}).get("summary", {})
    plugin_h = results.get("plugin_health", {}).get("summary", {})
    api_h = results.get("api_health", {}).get("summary", {})
    security = results.get("security", {}).get("summary", {})

    overall = round(
        (code_q.get("score", 0) + plugin_h.get("score", 0) +
         api_h.get("score", 0) + security.get("score", 0)) / 4
    )

    lines = [
        _SECTION_MARKER,
        f"- 마지막 점검: {now}",
        f"- 전체 건강도: {overall}/100",
        f"- 코드 품질: {code_q.get('score', 0)}/100 (pass:{code_q.get('pass', 0)} fail:{code_q.get('fail', 0)} warn:{code_q.get('warn', 0)})",
        f"- 플러그인: active {plugin_h.get('active', 0)}개 / fallback {plugin_h.get('fallback', 0)}개",
        f"- CASCADE 규칙: {plugin_h.get('cascade_rules', 0)}개 활성",
        f"- API 서비스: {api_h.get('services_ok', 0)}개 정상 / 환경변수 {api_h.get('env_configured', 0)}개 설정",
        f"- 보안 점수: {security.get('score', 0)}/100 (이슈 {security.get('issue_count', 0)}건)",
        "",
    ]

    # 보안 이슈 목록
    if security.get("issues"):
        lines.append("### 보안 주의사항")
        for issue in security["issues"]:
            lines.append(f"- {issue}")
        lines.append("")

    return "\n".join(lines)


def _generate_plugin_section(plugin_name: str, results: dict[str, Any]) -> str:
    """팀원 CLAUDE.md에 삽입할 에이전트 피드백 섹션을 생성합니다."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # 코드 품질에서 해당 플러그인 정보 추출
    code_results = results.get("code_quality", {}).get("interfaces", [])
    plugin_info = next((r for r in code_results if r["plugin"] == plugin_name), None)

    # 플러그인 상태에서 슬롯 정보 추출
    plugin_status = results.get("plugin_health", {}).get("plugin_status", {}).get("slots", {})

    lines = [
        _PLUGIN_SECTION_MARKER,
        f"- 점검 시각: {now}",
    ]

    if plugin_info:
        lines.append(f"- 인터페이스 점검: {plugin_info['status'].upper()}")
        for issue in plugin_info.get("issues", []):
            lines.append(f"  - {issue}")

    # 슬롯 매핑
    slot_map = {
        "food_rag": "food_agent", "exercise_weather": "exercise_agent",
        "health_checkup": "health_agent", "hobby_stress": "hobby_agent",
        "vision_korean": "image_analyzer", "voice_stt": "voice_processor",
    }
    slot = slot_map.get(plugin_name, "")
    if slot and slot in plugin_status:
        s = plugin_status[slot]
        lines.append(f"- 플러그인 상태: {s['status']} ({s['class']})")

    # CASCADE 활용 제안
    cascade = results.get("plugin_health", {}).get("cascade", {}).get("coverage", {})
    domain_map = {
        "food_rag": "food", "exercise_weather": "exercise",
        "health_checkup": "health", "hobby_stress": "hobby",
    }
    domain = domain_map.get(plugin_name, "")
    if domain and domain in cascade:
        targets = cascade[domain]["targets"]
        lines.append(f"- CASCADE 연결: {domain} -> {', '.join(targets)} ({len(targets)}개)")
    elif domain:
        lines.append("- CASCADE 연결: 없음 (오케스트레이터 활용 제안)")

    lines.append("")
    return "\n".join(lines)


def _update_file_section(filepath: Path, marker: str, new_content: str) -> bool:
    """파일에서 marker로 시작하는 섹션을 교체합니다. 없으면 끝에 추가합니다."""
    if not filepath.exists():
        logger.warning("[ClaudeMD] 파일 없음: %s", filepath)
        return False

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning("[ClaudeMD] 읽기 실패: %s - %s", filepath, e)
        return False

    if marker in content:
        # 기존 섹션 교체: marker부터 다음 ## 또는 파일 끝까지
        start = content.index(marker)
        rest = content[start + len(marker):]
        # 다음 ## 헤딩 찾기
        next_heading = rest.find("\n## ")
        if next_heading >= 0:
            end = start + len(marker) + next_heading
            updated = content[:start] + new_content + "\n" + content[end:]
        else:
            updated = content[:start] + new_content
    else:
        # 끝에 추가
        updated = content.rstrip() + "\n\n" + new_content

    try:
        filepath.write_text(updated, encoding="utf-8")
        logger.info("[ClaudeMD] 업데이트 완료: %s", filepath.name)
        return True
    except Exception as e:
        logger.warning("[ClaudeMD] 쓰기 실패: %s - %s", filepath, e)
        return False


def update_all(results: dict[str, Any]) -> dict[str, Any]:
    """모든 CLAUDE.md를 에이전트 결과로 업데이트합니다.

    Args:
        results: 코어 에이전트의 종합 결과.

    Returns:
        업데이트 결과 요약.
    """
    updated = {"root": False, "plugins": {}}

    # 루트 CLAUDE.md 업데이트
    root_section = _generate_root_section(results)
    updated["root"] = _update_file_section(_ROOT_CLAUDE_MD, _SECTION_MARKER, root_section)

    # 각 팀원 CLAUDE.md 업데이트
    plugin_folders = ["food_rag", "exercise_weather", "health_checkup",
                      "hobby_stress", "vision_korean", "voice_stt"]

    for folder in plugin_folders:
        claude_md = _PLUGINS_DIR / folder / "CLAUDE.md"
        if claude_md.exists():
            section = _generate_plugin_section(folder, results)
            updated["plugins"][folder] = _update_file_section(
                claude_md, _PLUGIN_SECTION_MARKER, section
            )
        else:
            updated["plugins"][folder] = False

    return updated
