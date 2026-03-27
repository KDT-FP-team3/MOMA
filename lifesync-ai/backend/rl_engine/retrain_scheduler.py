"""트리거 기반 + 시간 기반 자동 재학습 스케줄러.

트리거 조건(보상 하락, 피드백 저하) 외에 6시간 주기 시간 기반 재학습,
신뢰도 가중치 적용, 사용자별 보상 가중치 업데이트를 지원한다.
"""

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# 시간 기반 재학습 주기 (초)
RETRAIN_INTERVAL_SECONDS: int = 6 * 60 * 60  # 6시간


class RetrainScheduler:
    """모델 재학습 트리거 및 스케줄링.

    평균 보상이 임계값 아래로 떨어지거나
    사용자 피드백 점수가 하락하면 재학습을 트리거한다.
    추가로 6시간 주기 시간 기반 재학습, 신뢰도 가중치 적용,
    사용자별 보상 가중치 개인화를 지원한다.

    Attributes:
        threshold: 보상 하락 감지 임계 비율.
        retrain_interval: 시간 기반 재학습 주기(초).
        _recent_rewards: 최근 보상 기록.
        _recent_feedbacks: 최근 피드백 기록.
        _confidence_weights: 학습 데이터의 신뢰도 가중치 목록.
        _last_retrain_time: 마지막 재학습 시각(에폭 초).
        _user_reward_weights: 사용자별 보상 함수 가중치.
    """

    def __init__(
        self,
        threshold: float = 0.1,
        retrain_interval: int = RETRAIN_INTERVAL_SECONDS,
    ) -> None:
        self.threshold = threshold
        self.retrain_interval = retrain_interval
        self._recent_rewards: list[float] = []
        self._recent_feedbacks: list[float] = []
        self._confidence_weights: list[float] = []
        self._last_retrain_time: float = time.time()
        self._user_reward_weights: dict[str, dict[str, float]] = {}

    # ------------------------------------------------------------------
    # 신뢰도 가중치 관리
    # ------------------------------------------------------------------

    def add_confidence_weight(self, confidence_score: float) -> None:
        """학습 데이터 포인트에 대한 신뢰도 가중치를 추가한다.

        InputValidator가 산출한 confidence_score를 받아
        이후 재학습 시 해당 데이터의 가중치로 사용한다.

        Args:
            confidence_score: 0.0(확실히 잘못됨) ~ 1.0(완벽히 정상).
        """
        clamped = max(0.0, min(1.0, confidence_score))
        self._confidence_weights.append(clamped)

    def get_average_confidence(self) -> float:
        """현재 누적된 신뢰도 가중치의 평균을 반환한다.

        Returns:
            평균 신뢰도 점수. 데이터가 없으면 1.0.
        """
        if not self._confidence_weights:
            return 1.0
        return sum(self._confidence_weights) / len(self._confidence_weights)

    # ------------------------------------------------------------------
    # 사용자별 보상 가중치 관리
    # ------------------------------------------------------------------

    def update_user_reward_weights(
        self,
        user_id: str,
        feedback: dict[str, float],
    ) -> dict[str, float]:
        """사용자 피드백을 기반으로 개인화된 보상 가중치를 업데이트한다.

        R(s,a,t) = w1*r_taste + w2*r_health + w3*r_fitness + w4*r_mood + w5*r_habit
        각 축(taste, health, fitness, mood, habit)에 대한 피드백 만족도를
        반영하여 가중치를 조정한다.

        Args:
            user_id: 사용자 식별자.
            feedback: 도메인별 만족도 점수 딕셔너리.
                예: {"taste": 0.8, "health": 0.5, "fitness": 0.9,
                     "mood": 0.7, "habit": 0.6}

        Returns:
            업데이트된 사용자 보상 가중치 딕셔너리.
        """
        default_weights: dict[str, float] = {
            "taste": 0.2,
            "health": 0.25,
            "fitness": 0.2,
            "mood": 0.15,
            "habit": 0.2,
        }
        current = self._user_reward_weights.get(user_id, default_weights.copy())

        learning_rate = 0.1
        for domain, satisfaction in feedback.items():
            if domain in current:
                # 만족도가 낮은 도메인은 가중치를 높여 더 많이 최적화
                adjustment = learning_rate * (1.0 - satisfaction)
                current[domain] = current[domain] + adjustment

        # 정규화: 합이 1.0이 되도록
        total = sum(current.values())
        if total > 0:
            current = {k: round(v / total, 4) for k, v in current.items()}

        self._user_reward_weights[user_id] = current
        logger.info("사용자 %s 보상 가중치 업데이트: %s", user_id, current)
        return current

    def get_user_reward_weights(self, user_id: str) -> dict[str, float]:
        """사용자의 현재 보상 가중치를 반환한다.

        Args:
            user_id: 사용자 식별자.

        Returns:
            보상 가중치 딕셔너리. 미등록 사용자면 기본값 반환.
        """
        default_weights: dict[str, float] = {
            "taste": 0.2,
            "health": 0.25,
            "fitness": 0.2,
            "mood": 0.15,
            "habit": 0.2,
        }
        return self._user_reward_weights.get(user_id, default_weights.copy())

    # ------------------------------------------------------------------
    # 트리거 검사 (기존 + 시간 기반)
    # ------------------------------------------------------------------

    def check_trigger(self, metrics: dict[str, float]) -> bool:
        """재학습 트리거 조건 확인.

        기존 트리거(보상 하락, 피드백 저하)에 더해
        6시간 주기 시간 기반 트리거를 추가로 검사한다.

        Args:
            metrics: 현재 성능 지표 (avg_reward, feedback_score 등).

        Returns:
            True이면 재학습 필요.
        """
        avg_reward = metrics.get("avg_reward", 0.0)
        feedback_score = metrics.get("feedback_score", 3.0)

        self._recent_rewards.append(avg_reward)
        self._recent_feedbacks.append(feedback_score)

        # 시간 기반 트리거: 마지막 재학습 이후 retrain_interval 초 경과
        elapsed = time.time() - self._last_retrain_time
        if elapsed >= self.retrain_interval:
            logger.info(
                "재학습 트리거: 시간 기반 (%.1f시간 경과)",
                elapsed / 3600,
            )
            return True

        # 최근 10개 기준 보상 하락 감지
        if len(self._recent_rewards) >= 10:
            recent = self._recent_rewards[-10:]
            older = (
                self._recent_rewards[-20:-10]
                if len(self._recent_rewards) >= 20
                else recent
            )

            avg_recent = sum(recent) / len(recent)
            avg_older = sum(older) / len(older)

            if avg_older > 0 and (avg_older - avg_recent) / abs(avg_older) > self.threshold:
                logger.info(
                    "재학습 트리거: 보상 하락 %.2f → %.2f", avg_older, avg_recent
                )
                return True

        # 피드백 점수 하락
        if feedback_score < 2.0:
            logger.info("재학습 트리거: 피드백 점수 낮음 (%.1f)", feedback_score)
            return True

        return False

    # ------------------------------------------------------------------
    # 재학습 실행
    # ------------------------------------------------------------------

    def schedule_retrain(
        self,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """재학습 스케줄 실행.

        신뢰도 가중치가 낮은 데이터는 학습 시 가중치를 낮추고,
        사용자별 보상 가중치가 있으면 함께 전달한다.

        Args:
            user_id: 개인화 보상 가중치를 적용할 사용자 ID.
                None이면 기본 가중치 사용.

        Returns:
            재학습 스케줄 정보.
        """
        try:
            from backend.rl_engine.ppo_agent import PPOAgent
            from backend.rl_engine.auto_tuner import AutoTuner

            tuner = AutoTuner(n_trials=10)
            best_params = tuner.get_best_params()

            # 신뢰도 가중치 계산
            avg_confidence = self.get_average_confidence()
            # 낮은 신뢰도 → 학습 스텝 수 축소 (최소 1000)
            base_timesteps = 5000
            adjusted_timesteps = max(
                1000,
                int(base_timesteps * avg_confidence),
            )

            # 사용자별 보상 가중치
            reward_weights: dict[str, float] | None = None
            if user_id is not None:
                reward_weights = self.get_user_reward_weights(user_id)

            agent = PPOAgent()
            result = agent.train(total_timesteps=adjusted_timesteps)

            self._recent_rewards.clear()
            self._recent_feedbacks.clear()
            self._confidence_weights.clear()
            self._last_retrain_time = time.time()

            return {
                "status": "retrain_completed",
                "params": best_params,
                "training_result": result,
                "avg_confidence": round(avg_confidence, 4),
                "adjusted_timesteps": adjusted_timesteps,
                "reward_weights": reward_weights,
            }
        except Exception:
            logger.exception("재학습 실패")
            return {"status": "retrain_failed"}
