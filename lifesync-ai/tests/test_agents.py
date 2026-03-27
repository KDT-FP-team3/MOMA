"""에이전트 단위 테스트."""

import pytest

from backend.agents.food_agent import FoodAgent
from backend.agents.exercise_agent import ExerciseAgent
from backend.agents.health_agent import HealthAgent
from backend.agents.hobby_agent import HobbyAgent
from backend.agents.orchestrator import Orchestrator


class TestFoodAgent:
    """FoodAgent 단위 테스트."""

    def test_recommend_returns_dict(self) -> None:
        """레시피 추천 결과 구조 테스트."""
        agent = FoodAgent()
        result = agent.recommend({"bmi": 22, "calorie_target": 2000})

        assert isinstance(result, dict)
        assert "recommendations" in result
        assert "query" in result

    def test_analyze_nutrition_returns_dict(self) -> None:
        """영양 분석 결과 구조 테스트."""
        agent = FoodAgent()
        result = agent.analyze_nutrition(["김치찌개", "밥"])

        assert isinstance(result, dict)
        assert "calories" in result
        assert "protein" in result
        assert "fat" in result
        assert "carbs" in result
        assert result["calories"] > 0


class TestExerciseAgent:
    """ExerciseAgent 단위 테스트."""

    def test_recommend_returns_dict(self) -> None:
        """운동 추천 결과 구조 테스트."""
        agent = ExerciseAgent()
        result = agent.recommend({"bmi": 25, "goal": "체중 감량"})

        assert isinstance(result, dict)
        assert "exercises" in result

    def test_assess_injury_risk_range(self) -> None:
        """부상 위험도 범위 테스트 (0.0 ~ 1.0)."""
        agent = ExerciseAgent()
        risk = agent.assess_injury_risk("러닝", {"age": 30})

        assert isinstance(risk, float)
        assert 0.0 <= risk <= 1.0

    def test_injury_risk_increases_with_age(self) -> None:
        """나이 증가 시 부상 위험도 증가 테스트."""
        agent = ExerciseAgent()
        risk_young = agent.assess_injury_risk("러닝", {"age": 25})
        risk_old = agent.assess_injury_risk("러닝", {"age": 55})

        assert risk_old >= risk_young


class TestHealthAgent:
    """HealthAgent 단위 테스트."""

    def test_analyze_checkup_returns_dict(self) -> None:
        """건강검진 분석 결과 구조 테스트."""
        agent = HealthAgent()
        result = agent.analyze_checkup({"blood_pressure_sys": 130})

        assert isinstance(result, dict)
        assert "risk_level" in result

    def test_generate_health_plan_returns_dict(self) -> None:
        """건강 관리 플랜 결과 구조 테스트."""
        agent = HealthAgent()
        result = agent.generate_health_plan(
            {"stress_level": 75, "sleep_score": 40, "bmi": 27}
        )

        assert isinstance(result, dict)
        assert "concerns" in result
        assert "plan" in result
        assert len(result["concerns"]) > 0


class TestHobbyAgent:
    """HobbyAgent 단위 테스트."""

    def test_recommend_returns_dict(self) -> None:
        """취미 추천 결과 구조 테스트."""
        agent = HobbyAgent()
        result = agent.recommend({"stress_level": 70, "mood_score": 40})

        assert isinstance(result, dict)
        assert "hobbies" in result

    def test_estimate_stress_relief_range(self) -> None:
        """스트레스 해소 효과 범위 테스트."""
        agent = HobbyAgent()
        relief = agent.estimate_stress_relief("기타 연주", 30)

        assert isinstance(relief, float)
        assert 0.0 <= relief <= 1.0

    def test_stress_relief_increases_with_duration(self) -> None:
        """활동 시간 증가 시 스트레스 해소 효과 증가."""
        agent = HobbyAgent()
        short = agent.estimate_stress_relief("명상", 10)
        long = agent.estimate_stress_relief("명상", 30)

        assert long >= short


class TestOrchestrator:
    """Orchestrator 단위 테스트."""

    def test_run_chain_food(self) -> None:
        """food 도메인 연쇄 실행 테스트."""
        orch = Orchestrator()
        result = orch.run_chain("test_user", "food", {"meal_type": "점심"})

        assert result["user_id"] == "test_user"
        assert result["domain"] == "food"
        assert "result" in result
        assert "cascade_effects" in result

    def test_run_chain_invalid_domain(self) -> None:
        """잘못된 도메인 ValueError 테스트."""
        orch = Orchestrator()
        with pytest.raises(ValueError, match="Invalid domain"):
            orch.run_chain("test_user", "invalid", {})

    def test_cascade_effects_structure(self) -> None:
        """연쇄 효과 구조 테스트."""
        orch = Orchestrator()
        result = orch.run_chain("test_user", "hobby", {"stress_level": 70})

        cascade = result["cascade_effects"]
        assert "source_domain" in cascade
        assert "affected_domains" in cascade
        assert "effects" in cascade
        assert cascade["source_domain"] == "hobby"

    def test_all_domains_run(self) -> None:
        """모든 도메인 실행 가능 테스트."""
        orch = Orchestrator()
        for domain in Orchestrator.VALID_DOMAINS:
            result = orch.run_chain("test_user", domain, {})
            assert result["domain"] == domain
