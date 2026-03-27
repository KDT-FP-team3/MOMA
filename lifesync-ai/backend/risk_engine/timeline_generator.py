"""이벤트 타임라인 생성기 — 사용자 행동 기반 타임라인 구성."""

from datetime import datetime, timedelta, timezone
from typing import Any


class TimelineGenerator:
    """이벤트 타임라인 생성기."""

    def generate(
        self, events: list[dict[str, Any]], days: int = 7
    ) -> list[dict[str, Any]]:
        """이벤트 목록으로부터 타임라인 생성.

        Args:
            events: 이벤트 리스트 (각 이벤트: domain, action, timestamp, impact).
            days: 타임라인 범위 (일 수).

        Returns:
            일별로 그룹핑된 타임라인 리스트.
        """
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days)

        timeline: list[dict[str, Any]] = []

        for day_offset in range(days):
            day = start + timedelta(days=day_offset)
            day_str = day.strftime("%Y-%m-%d")

            day_events = [
                e for e in events
                if e.get("date", "") == day_str
            ]

            timeline.append(
                {
                    "date": day_str,
                    "day_of_week": day.strftime("%A"),
                    "events": day_events,
                    "summary": self._summarize_day(day_events),
                }
            )

        return timeline

    def generate_roadmap(
        self, goals: list[dict[str, Any]], weeks: int = 12
    ) -> list[dict[str, Any]]:
        """12주 로드맵 생성.

        Args:
            goals: 사용자 선택 목표 리스트.
            weeks: 로드맵 기간 (주).

        Returns:
            주별 로드맵 리스트.
        """
        roadmap: list[dict[str, Any]] = []

        for week in range(1, weeks + 1):
            phase = self._get_phase(week, weeks)
            week_plan = {
                "week": week,
                "phase": phase,
                "goals": [],
                "expected_progress": "",
            }

            for goal in goals:
                week_goal = self._scale_goal_for_week(goal, week, weeks)
                week_plan["goals"].append(week_goal)

            week_plan["expected_progress"] = self._estimate_progress(
                week, weeks
            )
            roadmap.append(week_plan)

        return roadmap

    def predict_impact(
        self, timeline: list[dict[str, Any]]
    ) -> dict[str, float]:
        """타임라인의 예상 영향도 계산.

        Args:
            timeline: 타임라인 데이터.

        Returns:
            도메인별 영향도 딕셔너리.
        """
        impact: dict[str, float] = {
            "food": 0.0,
            "exercise": 0.0,
            "health": 0.0,
            "hobby": 0.0,
        }

        for day in timeline:
            for event in day.get("events", []):
                domain = event.get("domain", "")
                event_impact = event.get("impact", 0.0)
                if domain in impact:
                    impact[domain] += event_impact

        return impact

    def _summarize_day(self, events: list[dict[str, Any]]) -> str:
        """일별 요약 생성."""
        if not events:
            return "활동 없음"

        domains = set(e.get("domain", "") for e in events)
        return f"{len(events)}개 활동 ({', '.join(domains)})"

    def _get_phase(self, week: int, total_weeks: int) -> str:
        """주차별 단계 결정."""
        ratio = week / total_weeks
        if ratio <= 0.17:
            return "적응기"
        if ratio <= 0.33:
            return "발전기"
        if ratio <= 0.67:
            return "강화기"
        return "완성기"

    def _scale_goal_for_week(
        self, goal: dict[str, Any], week: int, total_weeks: int
    ) -> dict[str, Any]:
        """목표를 주차에 맞게 조정."""
        intensity = min(1.0, week / (total_weeks * 0.7))
        return {
            "name": goal.get("name", ""),
            "domain": goal.get("domain", ""),
            "intensity": round(intensity, 2),
            "description": goal.get("description", ""),
        }

    def _estimate_progress(self, week: int, total_weeks: int) -> str:
        """주차별 예상 진행률."""
        progress = min(100, int((week / total_weeks) * 100))
        return f"목표 대비 {progress}% 진행"
