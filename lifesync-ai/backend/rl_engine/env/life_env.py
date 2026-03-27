"""LifeSync Gym 환경 — 40+ 차원 State 벡터 기반 강화학습 환경."""

from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from backend.rl_engine.reward_cross_domain import CrossDomainReward


# 10개 이산 행동 정의
ACTION_DEFINITIONS: list[dict[str, Any]] = [
    {"id": 0, "name": "healthy_meal", "domain": "food", "description": "건강한 식사"},
    {"id": 1, "name": "unhealthy_meal", "domain": "food", "description": "불건강한 식사"},
    {"id": 2, "name": "skip_meal", "domain": "food", "description": "식사 건너뛰기"},
    {"id": 3, "name": "cardio_exercise", "domain": "exercise", "description": "유산소 운동 30분"},
    {"id": 4, "name": "strength_exercise", "domain": "exercise", "description": "근력 운동 30분"},
    {"id": 5, "name": "skip_exercise", "domain": "exercise", "description": "운동 건너뛰기"},
    {"id": 6, "name": "health_check", "domain": "health", "description": "건강 체크"},
    {"id": 7, "name": "sleep_optimize", "domain": "health", "description": "수면 최적화"},
    {"id": 8, "name": "hobby_activity", "domain": "hobby", "description": "취미 활동 30분"},
    {"id": 9, "name": "rest", "domain": "hobby", "description": "휴식"},
]


class LifeEnv(gym.Env):
    """크로스 도메인 생활 관리 강화학습 환경.

    State: 40차원 벡터 (칼로리, 운동, 수면, 스트레스, BMI 등)
    Action: 10개 이산 행동 (도메인별 선택)
    Reward: CrossDomainReward 기반 다축 보상
    Episode: 84 스텝 (12주 x 7일)
    """

    metadata = {"render_modes": ["human"]}

    def __init__(self, state_dim: int = 40) -> None:
        super().__init__()
        self.state_dim = state_dim
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(state_dim,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(10)

        self._reward_fn = CrossDomainReward()
        self._state: np.ndarray = np.zeros(state_dim, dtype=np.float32)
        self._step_count: int = 0
        self._max_steps: int = 84  # 12주 x 7일

    def reset(
        self,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """환경 초기화.

        Returns:
            (observation, info) 튜플.
        """
        super().reset(seed=seed)
        self._step_count = 0

        # 기본 상태 초기화 (현실적 초기값)
        self._state = np.zeros(self.state_dim, dtype=np.float32)
        # 주요 필드 인덱스 매핑:
        # 0: calorie_intake, 1: calorie_burned, 2: sleep_score
        # 3: stress_level, 4: weight_kg, 5: bmi
        # 6: blood_pressure_sys, 7: blood_pressure_dia
        # 8: mood_score, 9: weekly_achievement
        self._state[0] = 2000.0   # calorie_intake
        self._state[1] = 200.0    # calorie_burned
        self._state[2] = 60.0     # sleep_score
        self._state[3] = 50.0     # stress_level
        self._state[4] = 75.0     # weight_kg
        self._state[5] = 25.0     # bmi
        self._state[6] = 120.0    # blood_pressure_sys
        self._state[7] = 80.0     # blood_pressure_dia
        self._state[8] = 50.0     # mood_score
        self._state[9] = 0.0      # weekly_achievement

        return self._state.copy(), {"step": 0}

    def step(
        self, action: int
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        """한 스텝 실행.

        Args:
            action: 행동 인덱스 (0-9).

        Returns:
            (observation, reward, terminated, truncated, info) 튜플.
        """
        self._step_count += 1
        action_def = ACTION_DEFINITIONS[action]

        # 행동에 따른 상태 전이
        self._apply_action(action, action_def)

        # 보상 계산
        state_dict = self._state_to_dict()
        action_dict = {
            "type": "meal" if action_def["domain"] == "food" else action_def["name"],
            "domain": action_def["domain"],
            "cooking_method": "healthy" if action == 0 else ("fried" if action == 1 else ""),
            "hobby_duration_min": 30 if action == 8 else 0,
            "health_check_done": action == 6,
            "skipped": action in (2, 5),
            "is_outdoor": False,
        }

        import time
        reward = self._reward_fn.compute(state_dict, action_dict, time.time())

        # 종료 조건
        terminated = self._step_count >= self._max_steps
        truncated = False

        info = {
            "step": self._step_count,
            "action_name": action_def["name"],
            "domain": action_def["domain"],
        }

        return self._state.copy(), reward, terminated, truncated, info

    def _apply_action(self, action: int, action_def: dict[str, Any]) -> None:
        """행동에 따른 상태 업데이트."""
        if action == 0:  # healthy_meal
            self._state[0] += 400     # calorie_intake
            self._state[8] += 2       # mood
            self._state[4] -= 0.02    # weight (미세 감소)
        elif action == 1:  # unhealthy_meal
            self._state[0] += 700     # calorie_intake
            self._state[8] += 5       # mood (단기 기분 상승)
            self._state[4] += 0.07    # weight 증가
            self._state[3] += 2       # stress (죄책감)
        elif action == 2:  # skip_meal
            self._state[8] -= 5       # mood 하락
            self._state[3] += 5       # stress 증가
        elif action == 3:  # cardio
            self._state[1] += 300     # calorie_burned
            self._state[2] += 3       # sleep 개선
            self._state[3] -= 5       # stress 감소
            self._state[4] -= 0.05    # weight 감소
        elif action == 4:  # strength
            self._state[1] += 200     # calorie_burned
            self._state[2] += 2       # sleep
            self._state[3] -= 3       # stress
        elif action == 5:  # skip_exercise
            self._state[3] += 3       # stress 증가
        elif action == 6:  # health_check
            self._state[8] += 3       # mood (안심감)
            self._state[3] -= 5       # stress 감소
        elif action == 7:  # sleep_optimize
            self._state[2] += 10      # sleep 크게 개선
            self._state[3] -= 5       # stress 감소
        elif action == 8:  # hobby
            self._state[3] -= 8       # stress 크게 감소
            self._state[8] += 5       # mood 상승
        elif action == 9:  # rest
            self._state[2] += 5       # sleep 소폭 개선
            self._state[3] -= 2       # stress 소폭 감소

        # BMI 재계산 (height 1.75m 가정)
        height_m = 1.75
        self._state[5] = self._state[4] / (height_m ** 2)

        # 주간 달성률 업데이트
        self._state[9] = self._step_count / self._max_steps

        # 클리핑
        self._state[2] = np.clip(self._state[2], 0, 100)   # sleep
        self._state[3] = np.clip(self._state[3], 0, 100)   # stress
        self._state[8] = np.clip(self._state[8], 0, 100)   # mood

    def _state_to_dict(self) -> dict[str, float]:
        """상태 벡터를 딕셔너리로 변환."""
        return {
            "calorie_intake": float(self._state[0]),
            "calorie_burned": float(self._state[1]),
            "sleep_score": float(self._state[2]),
            "stress_level": float(self._state[3]),
            "weight_kg": float(self._state[4]),
            "bmi": float(self._state[5]),
            "blood_pressure_sys": float(self._state[6]),
            "blood_pressure_dia": float(self._state[7]),
            "mood_score": float(self._state[8]),
            "weekly_achievement": float(self._state[9]),
        }
