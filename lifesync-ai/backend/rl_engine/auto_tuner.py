"""Optuna 하이퍼파라미터 자동 튜닝."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class AutoTuner:
    """Optuna 기반 하이퍼파라미터 최적화."""

    def __init__(self, n_trials: int = 100) -> None:
        self.n_trials = n_trials
        self._study: Any = None
        self._best_params: dict[str, Any] = {}

    def optimize(self, param_space: dict[str, Any] | None = None) -> dict[str, Any]:
        """하이퍼파라미터 최적화 실행.

        Args:
            param_space: 파라미터 탐색 공간 (미사용 시 기본값).

        Returns:
            최적 파라미터.
        """
        try:
            import optuna
            from stable_baselines3 import PPO
            from backend.rl_engine.env.life_env import LifeEnv

            def objective(trial: optuna.Trial) -> float:
                lr = trial.suggest_float("learning_rate", 1e-5, 1e-2, log=True)
                n_steps = trial.suggest_int("n_steps", 128, 2048, step=128)
                gamma = trial.suggest_float("gamma", 0.9, 0.999)
                batch_size = trial.suggest_categorical("batch_size", [32, 64, 128, 256])

                env = LifeEnv()
                model = PPO(
                    "MlpPolicy",
                    env,
                    learning_rate=lr,
                    n_steps=n_steps,
                    gamma=gamma,
                    batch_size=batch_size,
                    verbose=0,
                )
                model.learn(total_timesteps=1000)

                # 평가: 10 에피소드 평균 보상
                total_reward = 0.0
                for _ in range(10):
                    obs, _ = env.reset()
                    done = False
                    episode_reward = 0.0
                    while not done:
                        action, _ = model.predict(obs, deterministic=True)
                        obs, reward, terminated, truncated, _ = env.step(action)
                        episode_reward += reward
                        done = terminated or truncated
                    total_reward += episode_reward

                return total_reward / 10

            self._study = optuna.create_study(direction="maximize")
            self._study.optimize(objective, n_trials=self.n_trials, show_progress_bar=True)
            self._best_params = self._study.best_params

            logger.info("최적화 완료: best_value=%.2f", self._study.best_value)
            return self._best_params

        except ImportError:
            logger.warning("optuna 또는 stable-baselines3 미설치")
            return self._default_params()
        except Exception:
            logger.exception("하이퍼파라미터 최적화 실패")
            return self._default_params()

    def get_best_params(self) -> dict[str, Any]:
        """최적 하이퍼파라미터 반환."""
        if self._best_params:
            return self._best_params
        return self._default_params()

    def _default_params(self) -> dict[str, Any]:
        """기본 하이퍼파라미터."""
        return {
            "learning_rate": 3e-4,
            "n_steps": 256,
            "gamma": 0.99,
            "batch_size": 64,
        }
