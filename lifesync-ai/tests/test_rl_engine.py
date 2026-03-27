"""RL 엔진 단위 테스트."""

import time

import numpy as np
import pytest

from backend.rl_engine.env.life_env import LifeEnv
from backend.rl_engine.ppo_agent import PPOAgent
from backend.rl_engine.reward_cross_domain import (
    CrossDomainReward,
    PENALTY_NIGHT_MEAL,
    PENALTY_FRIED,
    PENALTY_OUTDOOR_DUST,
    BONUS_AIRFRYER,
    BONUS_HOBBY_30MIN,
    BONUS_HEALTH_CHECK,
    BONUS_PHOTO_50PCT,
)


class TestLifeEnv:
    """LifeEnv 단위 테스트."""

    def test_reset(self) -> None:
        """환경 초기화 테스트."""
        env = LifeEnv()
        obs, info = env.reset()
        assert obs.shape == (40,)
        assert info["step"] == 0
        assert obs.dtype == np.float32

    def test_step(self) -> None:
        """스텝 실행 테스트."""
        env = LifeEnv()
        env.reset()
        obs, reward, terminated, truncated, info = env.step(0)

        assert obs.shape == (40,)
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert info["step"] == 1

    def test_episode_termination(self) -> None:
        """에피소드 종료 (84 스텝) 테스트."""
        env = LifeEnv()
        env.reset()

        for i in range(84):
            obs, reward, terminated, truncated, info = env.step(0)

        assert terminated is True

    def test_action_space(self) -> None:
        """행동 공간 테스트."""
        env = LifeEnv()
        assert env.action_space.n == 10

    def test_observation_space(self) -> None:
        """관측 공간 테스트."""
        env = LifeEnv()
        assert env.observation_space.shape == (40,)


class TestPPOAgent:
    """PPOAgent 단위 테스트."""

    def test_predict_without_model(self) -> None:
        """모델 미로드 시 랜덤 예측."""
        agent = PPOAgent()
        state = np.zeros(40, dtype=np.float32)
        action, confidence = agent.predict(state)

        assert 0 <= action < 10
        assert isinstance(confidence, float)


class TestCrossDomainReward:
    """CrossDomainReward 단위 테스트."""

    def setup_method(self) -> None:
        """테스트 설정."""
        self.reward_fn = CrossDomainReward()

    def test_compute_basic(self) -> None:
        """기본 보상 계산 테스트."""
        state = {"taste_score": 1.0, "health_score": 1.0, "fitness_score": 1.0, "mood_score": 1.0, "habit_score": 1.0}
        action = {"type": "meal"}
        reward = self.reward_fn.compute(state, action, time.time())
        assert isinstance(reward, float)

    def test_night_meal_penalty(self) -> None:
        """야식 패널티 테스트 (23시)."""
        state = {}
        # 23시 타임스탬프 생성
        from datetime import datetime
        dt_23 = datetime(2024, 1, 1, 23, 0, 0)
        ts_23 = dt_23.timestamp()

        action = {"type": "meal"}
        penalty = self.reward_fn.compute_penalty(state, action, ts_23)
        assert penalty == PENALTY_NIGHT_MEAL  # -5.0

    def test_fried_food_penalty(self) -> None:
        """튀김 패널티 테스트."""
        state = {}
        action = {"cooking_method": "fried"}
        penalty = self.reward_fn.compute_penalty(state, action)
        assert penalty == PENALTY_FRIED  # -4.0

    def test_outdoor_dust_penalty(self) -> None:
        """미세먼지 야외 운동 패널티 테스트."""
        state = {"pm10": 80}
        action = {"is_outdoor": True}
        penalty = self.reward_fn.compute_penalty(state, action)
        assert penalty == PENALTY_OUTDOOR_DUST  # -4.0

    def test_no_penalty_indoor(self) -> None:
        """실내 운동 시 미세먼지 패널티 없음."""
        state = {"pm10": 80}
        action = {"is_outdoor": False}
        penalty = self.reward_fn.compute_penalty(state, action)
        assert penalty == 0.0

    def test_airfryer_bonus(self) -> None:
        """에어프라이어 보너스 테스트."""
        state = {}
        action = {"cooking_method": "airfryer"}
        bonus = self.reward_fn.compute_bonus(state, action)
        assert bonus == BONUS_AIRFRYER  # 2.0

    def test_hobby_30min_bonus(self) -> None:
        """취미 30분 이상 보너스 테스트."""
        state = {}
        action = {"hobby_duration_min": 30}
        bonus = self.reward_fn.compute_bonus(state, action)
        assert bonus == BONUS_HOBBY_30MIN  # 2.0

    def test_health_check_bonus(self) -> None:
        """건강검진 이행 보너스 테스트."""
        state = {}
        action = {"health_check_done": True}
        bonus = self.reward_fn.compute_bonus(state, action)
        assert bonus == BONUS_HEALTH_CHECK  # 4.0

    def test_photo_goal_bonus(self) -> None:
        """사진 목표 50% 달성 보너스 테스트."""
        state = {"photo_goal_progress": 0.6}
        action = {}
        bonus = self.reward_fn.compute_bonus(state, action)
        assert bonus == BONUS_PHOTO_50PCT  # 3.0

    def test_combined_penalties(self) -> None:
        """복합 패널티 테스트: 23시 + 튀김 + 미세먼지."""
        from datetime import datetime
        dt_23 = datetime(2024, 1, 1, 23, 0, 0)
        ts_23 = dt_23.timestamp()

        state = {"pm10": 80}
        action = {"type": "meal", "cooking_method": "fried", "is_outdoor": True}
        penalty = self.reward_fn.compute_penalty(state, action, ts_23)
        expected = PENALTY_NIGHT_MEAL + PENALTY_FRIED + PENALTY_OUTDOOR_DUST  # -13.0
        assert penalty == expected

    def test_skip_penalty(self) -> None:
        """스킵 패널티 테스트."""
        state = {}
        action = {"skipped": True}
        penalty = self.reward_fn.compute_penalty(state, action)
        assert penalty == -2.0
