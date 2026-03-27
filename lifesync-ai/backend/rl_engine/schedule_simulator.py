"""스케줄 기반 장기 시뮬레이션 엔진.

24시간 원형 시계 스케줄을 입력받아 N일간 시뮬레이션하고,
종합 건강 상태 변화, 문제점, 조언을 생성한다.
"""

import logging
import math
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# 활동 유형별 시간당 효과
ACTIVITY_EFFECTS: dict[str, dict[str, float]] = {
    "sleep": {
        "calorie_burned_per_h": 50,
        "sleep_score_per_h": 12.0,
        "stress_per_h": -3.0,
        "mood_per_h": 1.0,
        "weight_per_h": -0.002,
    },
    "meal_healthy": {
        "calorie_intake_per_h": 500,
        "mood_per_h": 3.0,
        "weight_per_h": -0.005,
        "stress_per_h": -1.0,
    },
    "meal_unhealthy": {
        "calorie_intake_per_h": 800,
        "mood_per_h": 5.0,
        "weight_per_h": 0.03,
        "stress_per_h": 1.5,
        "cholesterol_risk_per_h": 0.5,
    },
    "meal_normal": {
        "calorie_intake_per_h": 600,
        "mood_per_h": 2.0,
        "weight_per_h": 0.005,
        "stress_per_h": -0.5,
    },
    "night_snack": {
        "calorie_intake_per_h": 400,
        "sleep_score_per_h": -15.0,
        "weight_per_h": 0.05,
        "stress_per_h": 3.0,
        "mood_per_h": 3.0,
    },
    "exercise_cardio": {
        "calorie_burned_per_h": 500,
        "sleep_score_per_h": 5.0,
        "stress_per_h": -8.0,
        "mood_per_h": 5.0,
        "weight_per_h": -0.03,
    },
    "exercise_strength": {
        "calorie_burned_per_h": 350,
        "sleep_score_per_h": 3.0,
        "stress_per_h": -5.0,
        "mood_per_h": 4.0,
        "weight_per_h": -0.01,
    },
    "work": {
        "calorie_burned_per_h": 80,
        "stress_per_h": 4.0,
        "mood_per_h": -1.0,
    },
    "hobby": {
        "calorie_burned_per_h": 60,
        "stress_per_h": -6.0,
        "mood_per_h": 6.0,
    },
    "rest": {
        "calorie_burned_per_h": 50,
        "stress_per_h": -2.0,
        "mood_per_h": 2.0,
        "sleep_score_per_h": 2.0,
    },
    "commute": {
        "calorie_burned_per_h": 70,
        "stress_per_h": 3.0,
        "mood_per_h": -1.0,
    },
    "other": {
        "calorie_burned_per_h": 60,
        "stress_per_h": 0.0,
        "mood_per_h": 0.0,
    },
}

# 시간대 패널티/보너스
TIME_MODIFIERS: dict[str, Any] = {
    "night_snack_after_22": {"weight_multiplier": 1.5, "sleep_penalty": -10},
    "sleep_before_23": {"sleep_bonus": 5},
    "exercise_morning": {"mood_bonus": 3, "metabolism_boost": 1.1},
}


@dataclass
class ScheduleEntry:
    """스케줄 항목."""
    start_hour: int          # 0-23
    end_hour: int            # 0-24 (24 = 자정 넘김)
    activity: str            # 활동 유형 키
    label: str = ""          # 사용자 지정 라벨
    repeat_cycle: int = 1    # 반복 주기 (1=매일, 2=격일, 7=주1회 등)


@dataclass
class SimulationState:
    """시뮬레이션 상태."""
    weight_kg: float = 75.0
    bmi: float = 24.5
    sleep_score: float = 60.0
    stress_level: float = 50.0
    mood_score: float = 50.0
    calorie_intake: float = 0.0
    calorie_burned: float = 0.0
    exercise_hours_week: float = 0.0
    sleep_hours_avg: float = 7.0
    cholesterol_risk: float = 20.0
    hair_loss_risk: float = 20.0
    reactive_oxygen: float = 65.0
    blood_purity: float = 70.0


class ScheduleSimulator:
    """스케줄 기반 장기 시뮬레이션 엔진."""

    HEIGHT_M = 1.75  # 기본 신장

    def simulate(
        self,
        schedule: list[dict[str, Any]],
        days: int = 30,
        initial_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """스케줄 기반 장기 시뮬레이션 실행.

        Args:
            schedule: 스케줄 항목 리스트.
            days: 시뮬레이션 기간 (일).
            initial_state: 초기 건강 상태 (없으면 기본값).

        Returns:
            시뮬레이션 결과 (daily_states, final_state, analysis, advice).
        """
        entries = [ScheduleEntry(**e) for e in schedule]
        # repeat_cycle 검증: 0 이하면 1로 보정
        for entry in entries:
            if entry.repeat_cycle < 1:
                logger.warning(
                    "repeat_cycle=%d for '%s' is invalid; clamping to 1.",
                    entry.repeat_cycle, entry.activity,
                )
                entry.repeat_cycle = 1
        state = SimulationState(**(initial_state or {}))
        initial_snapshot = self._snapshot(state)

        daily_history: list[dict[str, Any]] = []
        weekly_exercise: float = 0.0

        for day in range(1, days + 1):
            daily_cal_in = 0.0
            daily_cal_out = 0.0
            daily_sleep = 0.0
            daily_exercise = 0.0

            for entry in entries:
                # 반복 주기 체크
                if (day - 1) % entry.repeat_cycle != 0:
                    continue

                duration = entry.end_hour - entry.start_hour
                if duration == 0:
                    continue
                if duration < 0:
                    duration += 24
                effects = ACTIVITY_EFFECTS.get(entry.activity, ACTIVITY_EFFECTS["other"])

                # 효과 적용
                cal_in = effects.get("calorie_intake_per_h", 0) * duration
                cal_out = effects.get("calorie_burned_per_h", 0) * duration
                sleep_delta = effects.get("sleep_score_per_h", 0) * duration
                stress_delta = effects.get("stress_per_h", 0) * duration
                mood_delta = effects.get("mood_per_h", 0) * duration
                weight_delta = effects.get("weight_per_h", 0) * duration
                chol_delta = effects.get("cholesterol_risk_per_h", 0) * duration

                daily_cal_in += cal_in
                daily_cal_out += cal_out

                # 시간대 보정
                if entry.activity == "night_snack" and entry.start_hour >= 22:
                    weight_delta *= 1.5
                    sleep_delta -= 10
                if entry.activity == "sleep" and entry.start_hour <= 23:
                    sleep_delta += 3
                if entry.activity.startswith("exercise") and entry.start_hour < 10:
                    mood_delta += 2

                # 수면 시간 트래킹
                if entry.activity == "sleep":
                    daily_sleep += duration
                if entry.activity.startswith("exercise"):
                    daily_exercise += duration

                # 상태 업데이트
                state.sleep_score = max(0, min(100, state.sleep_score + sleep_delta * 0.1))
                state.stress_level = max(0, min(100, state.stress_level + stress_delta * 0.1))
                state.mood_score = max(0, min(100, state.mood_score + mood_delta * 0.1))
                state.weight_kg += weight_delta
                state.cholesterol_risk = max(0, min(100, state.cholesterol_risk + chol_delta * 0.05))

            # 일별 칼로리 균형
            state.calorie_intake = daily_cal_in
            state.calorie_burned = daily_cal_out
            net_cal = daily_cal_in - daily_cal_out - 1800  # 기초대사량
            state.weight_kg += net_cal * 0.00013  # 7700kcal ≈ 1kg

            # BMI 재계산
            state.bmi = round(state.weight_kg / (self.HEIGHT_M ** 2), 1)

            # 수면 부족 연쇄
            state.sleep_hours_avg = daily_sleep
            if daily_sleep < 6:
                state.stress_level = min(100, state.stress_level + 3)
                state.mood_score = max(0, state.mood_score - 2)
                state.hair_loss_risk = min(100, state.hair_loss_risk + 0.3)

            # 운동 부족 연쇄
            weekly_exercise += daily_exercise
            if day % 7 == 0:
                state.exercise_hours_week = weekly_exercise
                if weekly_exercise < 2.5:
                    state.blood_purity = max(0, state.blood_purity - 2)
                    state.reactive_oxygen = max(0, state.reactive_oxygen - 1)
                else:
                    state.blood_purity = min(100, state.blood_purity + 1)
                    state.reactive_oxygen = min(100, state.reactive_oxygen + 1)
                weekly_exercise = 0.0

            # 스트레스-탈모 연쇄
            if state.stress_level > 70:
                state.hair_loss_risk = min(100, state.hair_loss_risk + 0.2)
            elif state.stress_level < 30:
                state.hair_loss_risk = max(5, state.hair_loss_risk - 0.1)

            # 기록
            daily_history.append({
                "day": day,
                "weight_kg": round(state.weight_kg, 2),
                "bmi": state.bmi,
                "sleep_score": round(state.sleep_score, 1),
                "stress_level": round(state.stress_level, 1),
                "mood_score": round(state.mood_score, 1),
                "calorie_intake": round(daily_cal_in),
                "calorie_burned": round(daily_cal_out),
                "sleep_hours": round(daily_sleep, 1),
                "exercise_hours": round(daily_exercise, 1),
                "hair_loss_risk": round(state.hair_loss_risk, 1),
                "blood_purity": round(state.blood_purity, 1),
                "reactive_oxygen": round(state.reactive_oxygen, 1),
            })

        final_snapshot = self._snapshot(state)
        analysis = self._analyze(initial_snapshot, final_snapshot, daily_history, entries, days)

        return {
            "days": days,
            "initial_state": initial_snapshot,
            "final_state": final_snapshot,
            "daily_history": daily_history,
            "analysis": analysis,
        }

    def _snapshot(self, state: SimulationState) -> dict[str, float]:
        """상태 스냅샷."""
        return {
            "weight_kg": round(state.weight_kg, 2),
            "bmi": round(state.bmi, 1),
            "sleep_score": round(state.sleep_score, 1),
            "stress_level": round(state.stress_level, 1),
            "mood_score": round(state.mood_score, 1),
            "hair_loss_risk": round(state.hair_loss_risk, 1),
            "blood_purity": round(state.blood_purity, 1),
            "reactive_oxygen": round(state.reactive_oxygen, 1),
            "cholesterol_risk": round(state.cholesterol_risk, 1),
            "exercise_hours_week": round(state.exercise_hours_week, 1),
            "sleep_hours_avg": round(state.sleep_hours_avg, 1),
        }

    def _analyze(
        self,
        initial: dict[str, float],
        final: dict[str, float],
        history: list[dict[str, Any]],
        entries: list[ScheduleEntry],
        days: int,
    ) -> dict[str, Any]:
        """결과 분석 — 문제점, 조언, 생활리듬 평가."""
        problems: list[dict[str, str]] = []
        advice: list[dict[str, str]] = []
        rhythm_score = 70  # 기본 생활리듬 점수

        # 체중 변화 분석
        weight_delta = final["weight_kg"] - initial["weight_kg"]
        if weight_delta > 2:
            problems.append({"category": "체중", "severity": "high", "message": f"체중이 {weight_delta:+.1f}kg 증가했습니다. 칼로리 과잉이 원인입니다."})
            advice.append({"category": "식단", "message": "하루 칼로리 섭취를 300kcal 줄이거나, 유산소 운동 30분을 추가하세요."})
        elif weight_delta < -3:
            problems.append({"category": "체중", "severity": "medium", "message": f"체중이 {weight_delta:+.1f}kg 급감했습니다. 영양 부족 가능성."})
            advice.append({"category": "식단", "message": "단백질 위주의 간식을 추가하고, 극단적 식이 제한을 피하세요."})

        # 수면 분석
        avg_sleep = sum(d["sleep_hours"] for d in history) / len(history)
        if avg_sleep < 6:
            problems.append({"category": "수면", "severity": "high", "message": f"평균 수면 {avg_sleep:.1f}시간 — 만성 수면 부족입니다."})
            advice.append({"category": "수면", "message": "최소 7시간 수면을 확보하세요. 취침 시간을 23시 이전으로 앞당기는 것을 권장합니다."})
            rhythm_score -= 15
        elif avg_sleep > 9:
            problems.append({"category": "수면", "severity": "low", "message": f"평균 수면 {avg_sleep:.1f}시간 — 과다 수면입니다."})
            advice.append({"category": "수면", "message": "수면 시간을 7-8시간으로 조절하세요. 과다 수면은 오히려 피로감을 유발합니다."})

        # 스트레스 분석
        if final["stress_level"] > 70:
            problems.append({"category": "스트레스", "severity": "high", "message": f"스트레스 {final['stress_level']:.0f}/100 — 매우 높은 수준입니다."})
            advice.append({"category": "스트레스", "message": "취미 활동을 하루 30분 이상 추가하세요. 명상, 기타 연주 등이 효과적입니다."})
            rhythm_score -= 10

        # 운동 분석
        avg_exercise = sum(d["exercise_hours"] for d in history) / len(history) * 7
        if avg_exercise < 2.5:
            problems.append({"category": "운동", "severity": "medium", "message": f"주간 운동 {avg_exercise:.1f}시간 — WHO 권장(2.5시간/주) 미달입니다."})
            advice.append({"category": "운동", "message": "주 3회 이상 유산소 운동 30분을 추가하세요."})
            rhythm_score -= 10
        elif avg_exercise >= 5:
            rhythm_score += 5

        # 야식 분석
        night_snacks = [e for e in entries if e.activity == "night_snack"]
        if night_snacks:
            freq = sum(1 for e in night_snacks for _ in range(days // max(1, e.repeat_cycle)))
            if freq > days * 0.3:
                problems.append({"category": "야식", "severity": "high", "message": f"야식 빈도가 높습니다 ({freq}회/{days}일). 수면과 체중에 악영향."})
                advice.append({"category": "야식", "message": "22시 이후 식사를 피하세요. 배가 고프면 삶은 달걀이나 따뜻한 물로 대체하세요."})
                rhythm_score -= 15

        # 생활 리듬 규칙성
        sleep_entries = [e for e in entries if e.activity == "sleep"]
        if sleep_entries:
            sleep_starts = [e.start_hour for e in sleep_entries]
            if max(sleep_starts) - min(sleep_starts) > 2:
                problems.append({"category": "생활리듬", "severity": "medium", "message": "취침 시간이 불규칙합니다. 일정한 시간에 잠자리에 드세요."})
                rhythm_score -= 10

        # 긍정적 요소
        hobby_entries = [e for e in entries if e.activity == "hobby"]
        if hobby_entries:
            rhythm_score += 5
            advice.append({"category": "취미", "message": "취미 활동이 스트레스 해소에 도움이 됩니다. 현재 루틴을 유지하세요."})

        # 종합 변화 요약
        changes: list[dict[str, Any]] = []
        for key in ["weight_kg", "sleep_score", "stress_level", "mood_score", "hair_loss_risk", "blood_purity"]:
            delta = final[key] - initial[key]
            if abs(delta) > 0.5:
                direction = "increase" if delta > 0 else "decrease"
                changes.append({"metric": key, "initial": initial[key], "final": final[key], "delta": round(delta, 1), "direction": direction})

        return {
            "problems": problems,
            "advice": advice,
            "changes": changes,
            "rhythm_score": max(0, min(100, rhythm_score)),
            "rhythm_grade": "우수" if rhythm_score >= 80 else "양호" if rhythm_score >= 60 else "주의" if rhythm_score >= 40 else "위험",
            "avg_sleep_hours": round(avg_sleep, 1),
            "avg_exercise_hours_week": round(avg_exercise, 1),
            "weight_change": round(weight_delta, 2),
        }
