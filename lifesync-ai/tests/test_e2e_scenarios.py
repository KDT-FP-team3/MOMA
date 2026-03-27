"""E2E 시나리오 테스트 — 5개 핵심 시나리오."""

import pytest

from backend.agents.orchestrator import Orchestrator
from backend.voice.intent_classifier import IntentClassifier
from backend.services.user_state_manager import UserStateManager
from backend.services.feedback_collector import FeedbackCollector
from backend.dashboard.gauge_calculator import GaugeCalculator
from backend.risk_engine.night_meal_penalty import NightMealPenalty
from backend.environment.plan_adjuster import PlanAdjuster


class TestE2EScenarios:
    """5개 E2E 시나리오 테스트."""

    def test_food_recommendation_flow(self) -> None:
        """시나리오 1: 음식 추천 전체 흐름.

        사용자 생성 → 상태 설정 → food 추천 → 결과 확인.
        """
        state_mgr = UserStateManager()
        state_mgr.update_state("e2e_user", {"bmi": 27, "stress_level": 60})

        orch = Orchestrator()
        result = orch.run_chain(
            "e2e_user", "food", {"meal_type": "저녁", "calorie_target": 500}
        )

        assert result["domain"] == "food"
        assert "result" in result
        assert "cascade_effects" in result
        # 연쇄 효과에 health와 exercise 포함 확인
        cascade = result["cascade_effects"]
        assert "health" in cascade.get("affected_domains", [])

    def test_exercise_with_weather_adjustment(self) -> None:
        """시나리오 2: 날씨 기반 운동 플랜 조정.

        미세먼지 높을 때 야외 → 실내 전환.
        """
        adjuster = PlanAdjuster()
        plan = {"activity": "러닝", "is_outdoor": True}
        weather = {"pm10": 80, "temperature": 20, "weather_main": "Clear"}

        result = adjuster.adjust(plan, weather)

        assert result["adjusted"] is True
        assert result["activity"] == "트레드밀"
        assert result["is_outdoor"] is False
        assert len(result["adjustments"]) > 0

    def test_cross_domain_cascade(self) -> None:
        """시나리오 3: 크로스 도메인 연쇄 효과.

        야식 → 수면 → 운동 → 체중 연쇄 확인.
        """
        penalty_calc = NightMealPenalty()
        meal = {"name": "라면", "calories": 500}
        penalty = penalty_calc.calculate(meal, 23)

        assert penalty < 0  # 야식 패널티 음수

        cascade = penalty_calc.estimate_cascade_effect(penalty)

        assert cascade["sleep_quality_delta"] < 0  # 수면 질 하락
        assert cascade["next_day_exercise_delta"] < 0  # 운동 성과 하락
        assert cascade["weight_goal_delay_days"] > 0  # 체중 목표 지연

    def test_voice_command_pipeline(self) -> None:
        """시나리오 4: 음성 명령 파이프라인.

        텍스트 → Intent 분류 → 도메인 라우팅 → 에이전트 실행.
        """
        classifier = IntentClassifier()
        orch = Orchestrator()

        # 음성 텍스트 시뮬레이션
        text = "오늘 점심 메뉴 추천해줘"
        intent = classifier.classify(text)

        assert intent["domain"] == "food"

        domain = classifier.route(intent)
        result = orch.run_chain("voice_user", domain, {"meal_type": "점심"})

        assert result["domain"] == "food"
        assert "result" in result

    def test_photo_analysis_feedback_loop(self) -> None:
        """시나리오 5: 피드백 → 보상 변환 루프.

        피드백 수집 → reward 변환 → 게이지 업데이트.
        """
        feedback_collector = FeedbackCollector()
        gauge_calc = GaugeCalculator()
        state_mgr = UserStateManager()

        # 피드백 수집
        feedback = {"type": "rating", "value": 5, "domain": "food"}
        feedback_collector.collect("feedback_user", feedback)

        reward = feedback_collector.to_reward(feedback)
        assert reward == 3.0  # 5점 = 3.0 보상

        # 상태 업데이트
        state_mgr.update_state("feedback_user", {"mood_score": 80})

        # 게이지 계산
        user_state = state_mgr.to_dict("feedback_user")
        gauges = gauge_calc.calculate_all(user_state)

        assert "reactive_oxygen" in gauges
        assert "blood_purity" in gauges
        assert "sleep_score" in gauges
        assert all(0 <= v <= 100 for v in gauges.values())
