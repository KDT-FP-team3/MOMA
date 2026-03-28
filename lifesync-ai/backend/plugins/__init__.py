# backend/plugins/ — 팀원별 플러그인 폴더
#
# 구조:
#   plugins/
#     __init__.py          (이 파일 — 자동 등록 로직)
#     food_rag/            (팀원 A — RAG 고도화)
#     exercise_weather/    (팀원 B — 운동+날씨 연동)
#     health_checkup/      (팀원 C — 건강검진 분석)
#     hobby_stress/        (팀원 D — 취미+스트레스 연동)
#     vision_korean/       (팀원 E — 한국 음식 YOLO)
#     voice_stt/           (팀원 F — 음성 파이프라인)
#
# 각 팀원은 자기 폴더만 수정하면 됩니다.
# 다른 팀원 폴더를 수정하면 안 됩니다.

import logging

logger = logging.getLogger(__name__)


def auto_register_plugins():
    """팀원 플러그인을 자동 검색하여 레지스트리에 등록.

    각 플러그인 폴더의 plugin.py에 register() 함수가 있으면 호출합니다.
    플러그인이 없거나 에러가 나도 서버는 정상 동작합니다 (폴백 사용).
    """
    from backend.core.plugin_registry import registry

    # 팀원 플러그인 폴더 → 슬롯 매핑
    _PLUGIN_MODULES = [
        "backend.plugins.food_rag.plugin",
        "backend.plugins.exercise_weather.plugin",
        "backend.plugins.health_checkup.plugin",
        "backend.plugins.hobby_stress.plugin",
        "backend.plugins.vision_korean.plugin",
        "backend.plugins.voice_stt.plugin",
    ]

    for module_path in _PLUGIN_MODULES:
        try:
            import importlib
            mod = importlib.import_module(module_path)
            if hasattr(mod, "register"):
                mod.register(registry)
                logger.info("플러그인 로드 성공: %s", module_path)
            else:
                logger.debug("register() 없음: %s (건너뜀)", module_path)
        except ImportError:
            # 팀원이 아직 구현하지 않음 → 폴백 사용
            logger.debug("플러그인 미구현: %s (폴백 사용)", module_path)
        except Exception as e:
            # 플러그인 에러 → 폴백 사용 (프로젝트에 영향 없음)
            logger.warning("플러그인 로드 실패: %s → %s (폴백 사용)", module_path, e)

    # 최종 상태 출력
    status = registry.status()
    active = sum(1 for v in status.values() if v["status"] == "plugin")
    total = len(status)
    logger.info("플러그인 상태: %d/%d 활성 (나머지 폴백)", active, total)
