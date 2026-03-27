"""Gamification service for LifeSync AI.

Manages user levels, EXP, badges, titles, and streaks.
Uses in-memory storage (dict) with planned Supabase integration.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_LEVEL: int = 50

# Exponential EXP table: level N requires N * 100 total cumulative EXP.
EXP_TABLE: list[int] = [n * 100 for n in range(MAX_LEVEL + 1)]  # index 0 unused

TITLE_BRACKETS: list[tuple[int, int, str]] = [
    (1, 9, "건강 새싹"),
    (10, 19, "생활 관리자"),
    (20, 29, "피트니스 워리어"),
    (30, 39, "건강 마스터"),
    (40, 50, "라이프 레전드"),
]

BADGE_DEFINITIONS: dict[str, str] = {
    "7일 연속 운동": "7일 연속으로 운동을 완료했습니다.",
    "야식 제로 1주": "1주일 동안 야식을 먹지 않았습니다.",
    "수면 점수 80+": "수면 점수 80 이상을 달성했습니다.",
    "첫 시뮬레이션": "첫 번째 시뮬레이션을 실행했습니다.",
    "레벨 10 달성": "레벨 10에 도달했습니다.",
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class UserProfile:
    """Represents a user's gamification profile."""

    user_id: str
    level: int = 1
    exp: int = 0
    badges: list[str] = field(default_factory=list)
    streak: int = 0
    exercise_streak: int = 0
    no_night_meal_streak: int = 0
    sleep_score_high: bool = False
    simulation_done: bool = False
    created_at: float = field(default_factory=time.time)


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_profiles: dict[str, UserProfile] = {}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _get_or_create_profile(user_id: str) -> UserProfile:
    """Return the profile for *user_id*, creating one if it does not exist.

    Args:
        user_id: Unique user identifier.

    Returns:
        The user's gamification profile.
    """
    if user_id not in _profiles:
        _profiles[user_id] = UserProfile(user_id=user_id)
    return _profiles[user_id]


def _exp_for_level(level: int) -> int:
    """Return the cumulative EXP required to reach *level*.

    Args:
        level: Target level (1-50).

    Returns:
        Cumulative EXP threshold.
    """
    if level < 1:
        return 0
    if level > MAX_LEVEL:
        return EXP_TABLE[MAX_LEVEL]
    return EXP_TABLE[level]


def _title_for_level(level: int) -> str:
    """Return the title string corresponding to *level*.

    Args:
        level: Current user level.

    Returns:
        Korean title string.
    """
    for low, high, title in TITLE_BRACKETS:
        if low <= level <= high:
            return title
    return TITLE_BRACKETS[-1][2]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def award_exp(user_id: str, action_type: str, amount: int) -> dict[str, Any]:
    """Add EXP to a user and handle level-up if applicable.

    Args:
        user_id: Unique user identifier.
        action_type: Category of the action (e.g. "exercise", "quest").
        amount: EXP points to award. Must be positive.

    Returns:
        Dict with keys: ``user_id``, ``action_type``, ``exp_gained``,
        ``total_exp``, ``level``, ``leveled_up``, ``title``.
    """
    if amount <= 0:
        raise ValueError("amount must be positive")

    profile = _get_or_create_profile(user_id)
    profile.exp += amount

    leveled_up = False
    while (
        profile.level < MAX_LEVEL
        and profile.exp >= _exp_for_level(profile.level + 1)
    ):
        profile.level += 1
        leveled_up = True

    # Auto-check badges after every EXP award.
    check_badges(user_id)

    return {
        "user_id": user_id,
        "action_type": action_type,
        "exp_gained": amount,
        "total_exp": profile.exp,
        "level": profile.level,
        "leveled_up": leveled_up,
        "title": _title_for_level(profile.level),
    }


def get_profile(user_id: str) -> dict[str, Any]:
    """Return the full gamification profile for a user.

    Args:
        user_id: Unique user identifier.

    Returns:
        Dict with keys: ``user_id``, ``level``, ``exp``, ``next_level_exp``,
        ``badges``, ``streak``, ``title``.
    """
    profile = _get_or_create_profile(user_id)
    next_level_exp = (
        _exp_for_level(profile.level + 1)
        if profile.level < MAX_LEVEL
        else _exp_for_level(MAX_LEVEL)
    )

    return {
        "user_id": profile.user_id,
        "level": profile.level,
        "exp": profile.exp,
        "next_level_exp": next_level_exp,
        "badges": list(profile.badges),
        "streak": profile.streak,
        "title": _title_for_level(profile.level),
    }


def check_badges(user_id: str) -> list[str]:
    """Check achievement conditions and award any newly earned badges.

    Args:
        user_id: Unique user identifier.

    Returns:
        List of badge names that were newly awarded in this call.
    """
    profile = _get_or_create_profile(user_id)
    newly_awarded: list[str] = []

    badge_checks: list[tuple[str, bool]] = [
        ("7일 연속 운동", profile.exercise_streak >= 7),
        ("야식 제로 1주", profile.no_night_meal_streak >= 7),
        ("수면 점수 80+", profile.sleep_score_high),
        ("첫 시뮬레이션", profile.simulation_done),
        ("레벨 10 달성", profile.level >= 10),
    ]

    for badge_name, condition in badge_checks:
        if condition and badge_name not in profile.badges:
            profile.badges.append(badge_name)
            newly_awarded.append(badge_name)

    return newly_awarded


# ---------------------------------------------------------------------------
# Profile attribute setters (for external services to trigger badge checks)
# ---------------------------------------------------------------------------

def record_exercise(user_id: str) -> None:
    """Increment the exercise streak for *user_id*.

    Args:
        user_id: Unique user identifier.
    """
    profile = _get_or_create_profile(user_id)
    profile.exercise_streak += 1
    profile.streak += 1
    check_badges(user_id)


def reset_exercise_streak(user_id: str) -> None:
    """Reset the exercise streak for *user_id* to zero.

    Args:
        user_id: Unique user identifier.
    """
    profile = _get_or_create_profile(user_id)
    profile.exercise_streak = 0


def record_no_night_meal(user_id: str) -> None:
    """Increment the no-night-meal streak for *user_id*.

    Args:
        user_id: Unique user identifier.
    """
    profile = _get_or_create_profile(user_id)
    profile.no_night_meal_streak += 1
    check_badges(user_id)


def reset_no_night_meal_streak(user_id: str) -> None:
    """Reset the no-night-meal streak for *user_id* to zero.

    Args:
        user_id: Unique user identifier.
    """
    profile = _get_or_create_profile(user_id)
    profile.no_night_meal_streak = 0


def record_sleep_score(user_id: str, score: float) -> None:
    """Record a sleep score and flag if it reaches 80+.

    Args:
        user_id: Unique user identifier.
        score: Sleep quality score (0-100).
    """
    profile = _get_or_create_profile(user_id)
    if score >= 80:
        profile.sleep_score_high = True
    check_badges(user_id)


def record_simulation(user_id: str) -> None:
    """Mark that the user has run their first simulation.

    Args:
        user_id: Unique user identifier.
    """
    profile = _get_or_create_profile(user_id)
    profile.simulation_done = True
    check_badges(user_id)
