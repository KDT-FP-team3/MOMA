"""Uncertainty estimation for RL simulation predictions.

Provides confidence intervals that grow over the forecast horizon,
reflecting increasing uncertainty in longer-term predictions.
"""

import math
from typing import Any


# Base standard deviations per metric (empirically calibrated).
# These represent the expected noise at the 1-week horizon.
DEFAULT_BASE_STD: dict[str, float] = {
    "weight_kg": 0.3,
    "sleep_score": 5.0,
    "stress_level": 7.0,
    "mood_score": 6.0,
    "bmi": 0.1,
}


class UncertaintyEstimator:
    """Estimate prediction uncertainty for simulation forecasts.

    Uncertainty grows proportionally to sqrt(day / 7), meaning that
    predictions further into the future carry wider confidence intervals.
    The 95% CI is computed as mean +/- 1.96 * std.

    Attributes:
        base_std: Mapping from metric name to its base standard deviation
            at the 1-week (7-day) horizon.
    """

    def __init__(
        self,
        base_std: dict[str, float] | None = None,
    ) -> None:
        """Initialize the uncertainty estimator.

        Args:
            base_std: Optional override for per-metric base standard
                deviations. If None, uses DEFAULT_BASE_STD.
        """
        self.base_std: dict[str, float] = (
            dict(base_std) if base_std is not None else dict(DEFAULT_BASE_STD)
        )

    def _compute_std(self, metric: str, day: int) -> float:
        """Compute the standard deviation for a metric at a given forecast day.

        Formula:
            std = base_std * sqrt(day / 7)

        Args:
            metric: The metric name (must exist in self.base_std).
            day: Forecast day (1-indexed).

        Returns:
            Standard deviation for the metric at the given day.
        """
        base = self.base_std.get(metric, 1.0)
        return base * math.sqrt(day / 7.0)

    def estimate(
        self,
        daily_history: list[dict[str, float]],
        forecast_days: int,
    ) -> list[dict[str, dict[str, float]]]:
        """Generate uncertainty estimates for each forecast day.

        For each day in the forecast horizon, computes the mean (from the
        last observed value), lower 95% CI, and upper 95% CI for every
        metric tracked in base_std.

        If daily_history is empty, uses 0.0 as the baseline mean for all
        metrics.

        Args:
            daily_history: List of daily observation dicts. Each dict maps
                metric names to their observed float values. The last entry
                is used as the baseline for forecasting.
            forecast_days: Number of days to forecast into the future.

        Returns:
            A list of length ``forecast_days``. Each element is a dict
            mapping metric names to a dict with keys:
                - "mean": The projected mean value.
                - "lower_95": Lower bound of the 95% confidence interval.
                - "upper_95": Upper bound of the 95% confidence interval.

        Raises:
            ValueError: If forecast_days is not positive.

        Example:
            >>> estimator = UncertaintyEstimator()
            >>> history = [{"weight_kg": 75.0, "sleep_score": 70.0}]
            >>> result = estimator.estimate(history, forecast_days=3)
            >>> result[0]["weight_kg"]["mean"]
            75.0
        """
        if forecast_days <= 0:
            raise ValueError(
                f"forecast_days must be positive, got {forecast_days}."
            )

        # Use the last observation as the baseline mean.
        if daily_history:
            baseline = daily_history[-1]
        else:
            baseline = {}

        forecasts: list[dict[str, dict[str, float]]] = []

        for day in range(1, forecast_days + 1):
            day_forecast: dict[str, dict[str, float]] = {}

            for metric in self.base_std:
                mean = baseline.get(metric, 0.0)
                std = self._compute_std(metric, day)
                margin = 1.96 * std

                day_forecast[metric] = {
                    "mean": mean,
                    "lower_95": mean - margin,
                    "upper_95": mean + margin,
                }

            forecasts.append(day_forecast)

        return forecasts

    def add_error_bars(
        self,
        simulation_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Augment a simulation result dict with error bar data.

        Expects ``simulation_result`` to contain a "daily_predictions" key
        whose value is a list of dicts (one per forecast day), each mapping
        metric names to predicted float values.

        Adds an "uncertainty" key to the result dict containing per-day,
        per-metric error bar information (std, lower_95, upper_95).

        Args:
            simulation_result: A dict with at least a "daily_predictions"
                key. The value should be a list of dicts mapping metric
                names to float values.

        Returns:
            The same dict with an added "uncertainty" key containing a
            list of per-day error bar dicts. Each day dict maps metric
            names to:
                - "std": Standard deviation at that forecast day.
                - "lower_95": Lower bound of the 95% CI.
                - "upper_95": Upper bound of the 95% CI.

        Raises:
            KeyError: If "daily_predictions" is missing from the input.

        Example:
            >>> estimator = UncertaintyEstimator()
            >>> sim = {
            ...     "daily_predictions": [
            ...         {"weight_kg": 74.8, "bmi": 24.1},
            ...         {"weight_kg": 74.6, "bmi": 24.0},
            ...     ]
            ... }
            >>> result = estimator.add_error_bars(sim)
            >>> "uncertainty" in result
            True
        """
        predictions: list[dict[str, float]] = simulation_result["daily_predictions"]
        uncertainty_data: list[dict[str, dict[str, float]]] = []

        for day_index, day_prediction in enumerate(predictions):
            day = day_index + 1  # 1-indexed day
            day_uncertainty: dict[str, dict[str, float]] = {}

            for metric, value in day_prediction.items():
                if metric not in self.base_std:
                    continue

                std = self._compute_std(metric, day)
                margin = 1.96 * std

                day_uncertainty[metric] = {
                    "std": std,
                    "lower_95": value - margin,
                    "upper_95": value + margin,
                }

            uncertainty_data.append(day_uncertainty)

        simulation_result["uncertainty"] = uncertainty_data
        return simulation_result
