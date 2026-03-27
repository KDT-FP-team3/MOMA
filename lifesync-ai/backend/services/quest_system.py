"""Daily quest system for LifeSync AI.

Generates random daily quests, tracks completion, and awards EXP
with streak bonuses. Uses in-memory storage.
"""

from __future__ import annotations

import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from backend.services.gamification import award_exp


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STREAK_BONUSES: list[tuple[int, int]] = [
    (7, 200),
    (3, 50),
]

DAILY_QUEST_COUNT: int = 3


# ---------------------------------------------------------------------------
# Quest pool
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class QuestTemplate:
    """Immutable definition of a quest type."""

    name: str
    description: str
    exp_reward: int
    category: str


QUEST_POOL: list[QuestTemplate] = [
    QuestTemplate("야채 포함 식사 2회", "하루에 야채가 포함된 식사를 2회 이상 하세요.", 20, "food"),
    QuestTemplate("운동 30분", "30분 이상 운동을 완료하세요.", 30, "exercise"),
    QuestTemplate("23시 전 취침", "밤 11시 이전에 잠자리에 드세요.", 25, "health"),
    QuestTemplate("물 8잔", "하루 동안 물을 8잔 이상 마시세요.", 15, "health"),
    QuestTemplate("스트레칭 10분", "10분 이상 스트레칭을 하세요.", 10, "exercise"),
    QuestTemplate("과일 섭취", "과일을 1회 이상 섭취하세요.", 15, "food"),
    QuestTemplate("계단 이용", "엘리베이터 대신 계단을 이용하세요.", 10, "exercise"),
    QuestTemplate("명상 5분", "5분 이상 명상을 하세요.", 20, "health"),
    QuestTemplate("단백질 섭취", "단백질이 포함된 식사를 하세요.", 15, "food"),
    QuestTemplate("만보 걷기", "하루 10,000보 이상 걸으세요.", 30, "exercise"),
    QuestTemplate("설탕 음료 제로", "설탕이 들어간 음료를 마시지 마세요.", 20, "food"),
    QuestTemplate("취미 활동 30분", "좋아하는 취미에 30분 이상 투자하세요.", 20, "hobby"),
    QuestTemplate("일기 쓰기", "오늘의 기분과 활동을 기록하세요.", 10, "health"),
    QuestTemplate("야식 참기", "밤 9시 이후 음식을 먹지 마세요.", 25, "food"),
    QuestTemplate("친구와 대화", "친구나 가족과 10분 이상 대화하세요.", 15, "hobby"),
    QuestTemplate("비타민 섭취", "비타민이나 영양제를 잊지 않고 복용하세요.", 10, "health"),
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Quest:
    """A concrete quest instance assigned to a user."""

    quest_id: str
    template: QuestTemplate
    completed: bool = False
    completed_at: float | None = None


@dataclass
class UserQuestState:
    """Tracks a user's daily quests and streak."""

    user_id: str
    quests: list[Quest] = field(default_factory=list)
    streak: int = 0
    last_completed_day: str = ""
    generated_day: str = ""


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_quest_states: dict[str, UserQuestState] = {}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _today() -> str:
    """Return today's date string in YYYY-MM-DD format.

    Returns:
        Date string for the current day.
    """
    return time.strftime("%Y-%m-%d", time.localtime())


def _get_or_create_state(user_id: str) -> UserQuestState:
    """Return the quest state for *user_id*, creating one if needed.

    Args:
        user_id: Unique user identifier.

    Returns:
        The user's quest state.
    """
    if user_id not in _quest_states:
        _quest_states[user_id] = UserQuestState(user_id=user_id)
    return _quest_states[user_id]


def _check_streak_bonus(user_id: str, streak: int) -> int:
    """Calculate and award streak bonus EXP.

    Args:
        user_id: Unique user identifier.
        streak: Current streak count (consecutive days).

    Returns:
        Bonus EXP awarded (0 if no bonus triggered).
    """
    for required_days, bonus_exp in STREAK_BONUSES:
        if streak > 0 and streak % required_days == 0:
            award_exp(user_id, "streak_bonus", bonus_exp)
            return bonus_exp
    return 0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_daily_quests(user_id: str) -> list[dict[str, Any]]:
    """Generate today's quests for a user.

    If quests have already been generated for today, returns the existing
    ones. Otherwise picks ``DAILY_QUEST_COUNT`` random quests from the pool.

    Args:
        user_id: Unique user identifier.

    Returns:
        List of quest dicts with keys: ``quest_id``, ``name``,
        ``description``, ``exp_reward``, ``category``, ``completed``.
    """
    state = _get_or_create_state(user_id)
    today = _today()

    if state.generated_day == today and state.quests:
        return _quests_to_dicts(state.quests)

    selected = random.sample(
        QUEST_POOL, min(DAILY_QUEST_COUNT, len(QUEST_POOL))
    )
    state.quests = [
        Quest(quest_id=str(uuid.uuid4()), template=tpl) for tpl in selected
    ]
    state.generated_day = today

    return _quests_to_dicts(state.quests)


def complete_quest(user_id: str, quest_id: str) -> dict[str, Any]:
    """Mark a quest as completed and award EXP.

    Args:
        user_id: Unique user identifier.
        quest_id: UUID of the quest to complete.

    Returns:
        Dict with keys: ``quest_id``, ``name``, ``exp_awarded``,
        ``streak``, ``streak_bonus``, ``all_completed``.

    Raises:
        ValueError: If *quest_id* is not found or already completed.
    """
    state = _get_or_create_state(user_id)

    quest: Quest | None = None
    for q in state.quests:
        if q.quest_id == quest_id:
            quest = q
            break

    if quest is None:
        raise ValueError(f"Quest {quest_id} not found for user {user_id}")
    if quest.completed:
        raise ValueError(f"Quest {quest_id} already completed")

    quest.completed = True
    quest.completed_at = time.time()

    # Award base EXP.
    exp_result = award_exp(user_id, "quest", quest.template.exp_reward)

    # Check if all daily quests are completed.
    all_completed = all(q.completed for q in state.quests)

    streak_bonus = 0
    if all_completed:
        today = _today()
        if state.last_completed_day == "":
            state.streak = 1
        else:
            # Simple consecutive-day check (works for same-timezone use).
            state.streak += 1
        state.last_completed_day = today
        streak_bonus = _check_streak_bonus(user_id, state.streak)

    return {
        "quest_id": quest_id,
        "name": quest.template.name,
        "exp_awarded": quest.template.exp_reward,
        "streak": state.streak,
        "streak_bonus": streak_bonus,
        "all_completed": all_completed,
    }


def get_quests(user_id: str) -> dict[str, Any]:
    """Return current quests with completion status.

    If no quests have been generated today, generates new ones first.

    Args:
        user_id: Unique user identifier.

    Returns:
        Dict with keys: ``user_id``, ``date``, ``streak``, ``quests``.
    """
    state = _get_or_create_state(user_id)
    today = _today()

    if state.generated_day != today or not state.quests:
        generate_daily_quests(user_id)

    return {
        "user_id": user_id,
        "date": state.generated_day,
        "streak": state.streak,
        "quests": _quests_to_dicts(state.quests),
    }


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def _quests_to_dicts(quests: list[Quest]) -> list[dict[str, Any]]:
    """Convert a list of Quest objects to serializable dicts.

    Args:
        quests: List of Quest instances.

    Returns:
        List of dicts suitable for JSON serialization.
    """
    return [
        {
            "quest_id": q.quest_id,
            "name": q.template.name,
            "description": q.template.description,
            "exp_reward": q.template.exp_reward,
            "category": q.template.category,
            "completed": q.completed,
        }
        for q in quests
    ]
