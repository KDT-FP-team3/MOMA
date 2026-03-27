"""PPO 정책 에이전트 — Stable-Baselines3 기반 PPO 학습 및 추론."""

import logging
import os
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class PPOAgent:
    """PPO 강화학습 에이전트."""

    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = model_path
        self._model: Any = None

        if model_path and os.path.exists(model_path):
            self.load(model_path)

    def train(self, total_timesteps: int = 10000) -> dict[str, Any]:
        """PPO 모델 학습.

        Args:
            total_timesteps: 총 학습 타임스텝.

        Returns:
            학습 결과 메트릭.
        """
        try:
            from stable_baselines3 import PPO
            from backend.rl_engine.env.life_env import LifeEnv

            env = LifeEnv()
            self._model = PPO(
                "MlpPolicy",
                env,
                verbose=1,
                learning_rate=3e-4,
                n_steps=128,
                batch_size=64,
                n_epochs=10,
                gamma=0.99,
            )
            self._model.learn(total_timesteps=total_timesteps)

            logger.info("PPO 학습 완료: %d 타임스텝", total_timesteps)
            return {
                "total_timesteps": total_timesteps,
                "status": "completed",
            }
        except ImportError:
            logger.warning("stable-baselines3 패키지 미설치")
            return {"status": "skipped", "reason": "stable-baselines3 미설치"}
        except Exception:
            logger.exception("PPO 학습 실패")
            return {"status": "failed"}

    def predict(self, state: np.ndarray) -> tuple[int, float]:
        """상태 벡터로부터 행동 예측.

        Args:
            state: 40차원 상태 벡터.

        Returns:
            (action_index, confidence) 튜플.
        """
        if self._model is None:
            # 모델 미로드 시 랜덤 행동
            return int(np.random.randint(0, 10)), 0.1

        try:
            action, _states = self._model.predict(state, deterministic=True)
            return int(action), 0.8
        except Exception:
            logger.exception("PPO 예측 실패")
            return int(np.random.randint(0, 10)), 0.1

    def save(self, path: str) -> None:
        """모델 저장."""
        if self._model is not None:
            self._model.save(path)
            logger.info("PPO 모델 저장: %s", path)

    def load(self, path: str) -> None:
        """모델 로드."""
        try:
            from stable_baselines3 import PPO
            self._model = PPO.load(path)
            logger.info("PPO 모델 로드: %s", path)
        except ImportError:
            logger.warning("stable-baselines3 패키지 미설치")
        except Exception:
            logger.exception("PPO 모델 로드 실패: %s", path)
