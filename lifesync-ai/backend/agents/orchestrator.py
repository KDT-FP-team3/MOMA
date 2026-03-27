"""크로스 도메인 연쇄 엔진 — LangGraph StateGraph 기반 오케스트레이션.

4개 도메인 에이전트를 LangGraph 그래프로 연결하고,
크로스 도메인 연쇄 효과를 노드 간 엣지로 처리한다.
"""

import logging
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END

from backend.agents.food_agent import FoodAgent
from backend.agents.exercise_agent import ExerciseAgent
from backend.agents.health_agent import HealthAgent
from backend.agents.hobby_agent import HobbyAgent

logger = logging.getLogger(__name__)


# --- LangGraph 상태 정의 ---
class ChainState(TypedDict):
    """LangGraph 상태 스키마."""

    user_id: str
    domain: str
    action: dict[str, Any]
    result: dict[str, Any]
    cascade_effects: dict[str, Any]
    affected_domains: list[str]


# --- 크로스 도메인 연쇄 규칙 ---
CASCADE_RULES: dict[str, dict[str, dict[str, Any]]] = {
    "food": {
        "health": {
            "description": "음식 → 건강: 칼로리/영양 영향",
            "compute": lambda r: {
                "calorie_impact": r.get("calories", 0),
                "cholesterol_risk_delta": 0.12 if r.get("cooking_method") in ("fried", "deep_fried", "튀김") else 0.0,
            },
        },
        "exercise": {
            "description": "음식 → 운동: 칼로리 초과 시 추가 운동 필요",
            "compute": lambda r: {
                "extra_exercise_min": max(0, (r.get("calories", 0) - 500) / 10),
            },
        },
    },
    "exercise": {
        "health": {
            "description": "운동 → 건강: 수면 개선, 스트레스 감소",
            "compute": lambda r: {
                "sleep_improvement": min(15, r.get("duration_min", 0) * 0.3),
                "stress_reduction": min(20, r.get("duration_min", 0) * 0.4),
            },
        },
        "food": {
            "description": "운동 → 음식: 운동 후 단백질 식사 권장",
            "compute": lambda r: {
                "protein_recommendation": r.get("calories_burned", 0) > 200,
                "hydration_needed_ml": r.get("duration_min", 0) * 10,
            },
        },
    },
    "health": {
        "exercise": {
            "description": "건강 → 운동: 건강 상태에 따른 운동 강도 조절",
            "compute": lambda r: {
                "intensity_adjustment": -0.3 if r.get("risk_level") == "high" else 0.0,
            },
        },
        "food": {
            "description": "건강 → 음식: 건강 위험 시 식단 제한",
            "compute": lambda r: {
                "dietary_restriction": r.get("risk_level", "low") != "low",
            },
        },
    },
    "hobby": {
        "health": {
            "description": "취미 → 건강: 스트레스 해소 효과",
            "compute": lambda r: {
                "stress_reduction": r.get("stress_relief", 0.5) * 15,
                "mood_improvement": r.get("stress_relief", 0.5) * 10,
            },
        },
        "food": {
            "description": "취미 → 음식: 폭식 충동 감소",
            "compute": lambda r: {
                "binge_impulse_reduction": r.get("stress_relief", 0.5) * 0.4,
            },
        },
        "exercise": {
            "description": "취미 → 운동: 운동 동기부여",
            "compute": lambda r: {
                "motivation_boost": r.get("stress_relief", 0.5) * 0.2,
            },
        },
    },
}


class Orchestrator:
    """LangGraph 기반 크로스 도메인 오케스트레이터.

    StateGraph를 사용하여 4개 도메인 에이전트를 그래프로 연결하고,
    도메인 라우팅 → 에이전트 실행 → 연쇄 효과 계산 파이프라인을 구성한다.
    """

    VALID_DOMAINS: list[str] = ["food", "exercise", "health", "hobby"]

    def __init__(self) -> None:
        self.food_agent = FoodAgent()
        self.exercise_agent = ExerciseAgent()
        self.health_agent = HealthAgent()
        self.hobby_agent = HobbyAgent()

        # LangGraph 그래프 구성
        self._graph = self._build_graph()

    def _build_graph(self) -> Any:
        """LangGraph StateGraph 구성.

        그래프 구조:
          route_domain → execute_agent → compute_cascade → END
        """
        graph = StateGraph(ChainState)

        # 노드 등록
        graph.add_node("route_domain", self._route_domain_node)
        graph.add_node("execute_agent", self._execute_agent_node)
        graph.add_node("compute_cascade", self._compute_cascade_node)

        # 엣지 연결
        graph.set_entry_point("route_domain")
        graph.add_edge("route_domain", "execute_agent")
        graph.add_edge("execute_agent", "compute_cascade")
        graph.add_edge("compute_cascade", END)

        return graph.compile()

    def run_chain(
        self, user_id: str, domain: str, action: dict[str, Any]
    ) -> dict[str, Any]:
        """크로스 도메인 연쇄 실행.

        Args:
            user_id: 사용자 식별자.
            domain: 대상 도메인 ("food" | "exercise" | "health" | "hobby").
            action: 도메인별 행동 파라미터.

        Returns:
            에이전트 실행 결과 및 크로스 도메인 연쇄 효과.

        Raises:
            ValueError: 유효하지 않은 도메인인 경우.
        """
        if domain not in self.VALID_DOMAINS:
            raise ValueError(
                f"Invalid domain: {domain}. Must be one of {self.VALID_DOMAINS}"
            )

        logger.info("run_chain 호출: user=%s, domain=%s", user_id, domain)

        # LangGraph 실행
        initial_state: ChainState = {
            "user_id": user_id,
            "domain": domain,
            "action": action,
            "result": {},
            "cascade_effects": {},
            "affected_domains": [],
        }

        final_state = self._graph.invoke(initial_state)

        return {
            "user_id": final_state["user_id"],
            "domain": final_state["domain"],
            "result": final_state["result"],
            "cascade_effects": final_state["cascade_effects"],
        }

    # --- LangGraph 노드 함수 ---

    def _route_domain_node(self, state: ChainState) -> ChainState:
        """도메인 라우팅 노드 — 유효성 검증 및 로깅."""
        domain = state["domain"]
        logger.info("[LangGraph] route_domain: %s", domain)
        return state

    def _execute_agent_node(self, state: ChainState) -> ChainState:
        """에이전트 실행 노드 — 도메인별 에이전트 호출."""
        domain = state["domain"]
        action = state["action"]

        logger.info("[LangGraph] execute_agent: domain=%s", domain)

        if domain == "food":
            result = self.food_agent.recommend(action)
        elif domain == "exercise":
            result = self.exercise_agent.recommend(action)
        elif domain == "health":
            result = self.health_agent.analyze_checkup(action)
        elif domain == "hobby":
            result = self.hobby_agent.recommend(action)
        else:
            result = {}

        return {**state, "result": result}

    def _compute_cascade_node(self, state: ChainState) -> ChainState:
        """연쇄 효과 계산 노드 — 크로스 도메인 전파."""
        source_domain = state["domain"]
        result = state["result"]

        logger.info("[LangGraph] compute_cascade: source=%s", source_domain)

        domain_rules = CASCADE_RULES.get(source_domain, {})
        effects: dict[str, Any] = {}

        for target_domain, rule in domain_rules.items():
            try:
                compute_fn = rule.get("compute")
                if compute_fn:
                    effect = compute_fn(result)
                    effects[target_domain] = {
                        "description": rule.get("description", ""),
                        "effects": effect,
                    }
            except Exception:
                logger.exception(
                    "연쇄 효과 계산 실패: %s → %s", source_domain, target_domain
                )

        cascade = {
            "source_domain": source_domain,
            "affected_domains": list(effects.keys()),
            "effects": effects,
        }

        return {**state, "cascade_effects": cascade, "affected_domains": list(effects.keys())}
