"""로컬 GPU 학습 → 모델 업로드 스크립트.

Usage:
    python scripts/train_and_upload.py --timesteps 50000 --optimize
    python scripts/train_and_upload.py --timesteps 10000  # 빠른 학습

이 스크립트는 로컬(GPU/CPU)에서 PPO 학습을 수행하고,
학습된 모델을 서버(Railway)에 업로드하여
웹/앱 클라이언트가 최신 가중치를 동기화할 수 있게 한다.
"""

import argparse
import json
import logging
import os
import sys
import time

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def train_ppo(timesteps: int, optimize: bool = False) -> dict:
    """PPO 학습 실행.

    Args:
        timesteps: 총 학습 타임스텝.
        optimize: True면 Optuna로 하이퍼파라미터 최적화 후 학습.

    Returns:
        학습 결과 딕셔너리.
    """
    from backend.rl_engine.env.life_env import LifeEnv

    best_params = {
        "learning_rate": 3e-4,
        "n_steps": 256,
        "gamma": 0.99,
        "batch_size": 64,
    }

    # Optuna 최적화 (선택)
    if optimize:
        logger.info("Optuna 하이퍼파라미터 최적화 시작...")
        from backend.rl_engine.auto_tuner import AutoTuner
        tuner = AutoTuner(n_trials=20)
        best_params = tuner.optimize()
        logger.info("최적 파라미터: %s", best_params)

    # PPO 학습
    logger.info("PPO 학습 시작: %d 타임스텝, params=%s", timesteps, best_params)

    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.callbacks import EvalCallback

        env = LifeEnv()
        eval_env = LifeEnv()

        model = PPO(
            "MlpPolicy",
            env,
            learning_rate=best_params["learning_rate"],
            n_steps=best_params["n_steps"],
            gamma=best_params["gamma"],
            batch_size=best_params["batch_size"],
            n_epochs=10,
            verbose=1,
        )

        # 평가 콜백
        os.makedirs("models/ppo_policy", exist_ok=True)
        eval_callback = EvalCallback(
            eval_env,
            best_model_save_path="models/ppo_policy/",
            log_path="models/ppo_policy/logs/",
            eval_freq=max(1000, timesteps // 10),
            deterministic=True,
        )

        start = time.time()
        model.learn(total_timesteps=timesteps, callback=eval_callback)
        elapsed = time.time() - start

        # 최종 모델 저장
        model_path = "models/ppo_policy/final_model.zip"
        model.save(model_path)

        # 평가
        total_reward = 0
        for _ in range(20):
            obs, _ = eval_env.reset()
            done = False
            ep_reward = 0
            while not done:
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, _ = eval_env.step(action)
                ep_reward += reward
                done = terminated or truncated
            total_reward += ep_reward

        avg_reward = total_reward / 20

        result = {
            "status": "completed",
            "timesteps": timesteps,
            "elapsed_sec": round(elapsed, 1),
            "avg_reward_20ep": round(avg_reward, 2),
            "model_path": model_path,
            "params": best_params,
        }
        logger.info("학습 완료: %.1f초, 평균 보상: %.2f", elapsed, avg_reward)
        return result

    except ImportError as e:
        logger.error("필수 패키지 미설치: %s", e)
        logger.error("pip install stable-baselines3 optuna")
        return {"status": "error", "detail": str(e)}


def upload_to_server(model_path: str, server_url: str) -> dict:
    """학습된 모델을 서버에 업로드.

    Args:
        model_path: 로컬 모델 파일 경로.
        server_url: Railway 서버 URL.

    Returns:
        업로드 결과.
    """
    import httpx

    logger.info("서버에 업로드: %s → %s", model_path, server_url)

    with open(model_path, "rb") as f:
        response = httpx.post(
            f"{server_url}/api/models/upload",
            params={"model_name": "ppo_policy"},
            files={"file": (os.path.basename(model_path), f)},
            timeout=120.0,
        )

    if response.status_code == 200:
        result = response.json()
        logger.info("업로드 성공: version=%s", result.get("version"))
        return result
    else:
        logger.error("업로드 실패: %d %s", response.status_code, response.text)
        return {"status": "error", "code": response.status_code}


def upload_to_s3(model_path: str) -> dict:
    """S3에 직접 업로드 (서버 경유 없이).

    Args:
        model_path: 로컬 모델 파일 경로.

    Returns:
        업로드 결과.
    """
    from backend.services.model_registry import ModelRegistry
    registry = ModelRegistry()
    return registry.upload_model("ppo_policy", model_path, metadata={"source": "local_gpu"})


def main():
    parser = argparse.ArgumentParser(description="LifeSync AI — GPU 학습 + 모델 업로드")
    parser.add_argument("--timesteps", type=int, default=10000, help="학습 타임스텝 (기본: 10000)")
    parser.add_argument("--optimize", action="store_true", help="Optuna 하이퍼파라미터 최적화 활성화")
    parser.add_argument("--upload-server", type=str, default="", help="Railway 서버 URL (예: https://moma-production.up.railway.app)")
    parser.add_argument("--upload-s3", action="store_true", help="S3에 직접 업로드")
    parser.add_argument("--skip-train", action="store_true", help="학습 건너뛰고 업로드만")
    args = parser.parse_args()

    # 1. 학습
    if not args.skip_train:
        result = train_ppo(args.timesteps, args.optimize)
        if result["status"] != "completed":
            logger.error("학습 실패: %s", result)
            sys.exit(1)

        # 결과 저장
        with open("models/ppo_policy/train_result.json", "w") as f:
            json.dump(result, f, indent=2)

        model_path = result["model_path"]
    else:
        model_path = "models/ppo_policy/final_model.zip"

    # 2. 업로드
    if args.upload_server:
        upload_to_server(model_path, args.upload_server)

    if args.upload_s3:
        upload_to_s3(model_path)

    if not args.upload_server and not args.upload_s3:
        logger.info("모델 저장 위치: %s", model_path)
        logger.info("서버 업로드: --upload-server https://moma-production.up.railway.app")
        logger.info("S3 업로드: --upload-s3")


if __name__ == "__main__":
    main()
