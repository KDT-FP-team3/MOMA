"""크로스 도메인 연쇄 엔진 — LangGraph StateGraph 기반 오케스트레이션.

4개 도메인 에이전트를 LangGraph 그래프로 연결하고,
조건 분기와 대화 메모리를 통해 크로스 도메인 연쇄 효과를 처리한다.

그래프 구조:
  classify_intent
      ↓ (조건 분기)
  ┌── food_agent ──┐
  ├── exercise_agent ┤
  ├── health_agent ──┤→ merge_results → compute_cascade → evaluate → END
  └── hobby_agent ──┘
"""

import logging
from typing import Any, Literal, TypedDict

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
    # 멀티 도메인 지원
    target_domains: list[str]
    multi_results: dict[str, Any]
    # 대화 히스토리
    history: list[dict[str, Any]]
    # 평가 메트릭
    evaluation: dict[str, Any]


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

# 키워드 → 도메인 매핑 (멀티 도메인 인텐트 분류용)
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "food": ["식사", "음식", "요리", "레시피", "칼로리", "식단", "먹", "밥", "메뉴", "영양", "다이어트"],
    "exercise": ["운동", "헬스", "달리기", "러닝", "근력", "유산소", "스트레칭", "걷기", "조깅"],
    "health": ["건강", "검진", "혈압", "콜레스테롤", "수면", "스트레스", "체중", "BMI", "혈액"],
    "hobby": ["취미", "기타", "독서", "명상", "그림", "음악", "게임", "산책", "여행"],
}


class Orchestrator:
    """LangGraph 기반 크로스 도메인 오케스트레이터.

    조건 분기, 멀티 도메인 실행, 대화 메모리를 지원한다.
    """

    VALID_DOMAINS: list[str] = ["food", "exercise", "health", "hobby"]

    def __init__(self) -> None:
        self.food_agent = FoodAgent()
        self.exercise_agent = ExerciseAgent()
        self.health_agent = HealthAgent()
        self.hobby_agent = HobbyAgent()

        # 사용자별 대화 히스토리 (메모리)
        self._memory: dict[str, list[dict[str, Any]]] = {}

        # LangGraph 그래프 구성
        self._graph = self._build_graph()

    def _build_graph(self) -> Any:
        """조건 분기 + 멀티 도메인 LangGraph 구성."""
        graph = StateGraph(ChainState)

        # 노드 등록
        graph.add_node("classify_intent", self._classify_intent_node)
        graph.add_node("food_agent", self._food_agent_node)
        graph.add_node("exercise_agent", self._exercise_agent_node)
        graph.add_node("health_agent", self._health_agent_node)
        graph.add_node("hobby_agent", self._hobby_agent_node)
        graph.add_node("merge_results", self._merge_results_node)
        graph.add_node("compute_cascade", self._compute_cascade_node)
        graph.add_node("evaluate", self._evaluate_node)

        # 진입점
        graph.set_entry_point("classify_intent")

        # 조건 분기: 인텐트에 따라 에이전트 선택
        graph.add_conditional_edges(
            "classify_intent",
            self._route_to_agent,
            {
                "food": "food_agent",
                "exercise": "exercise_agent",
                "health": "health_agent",
                "hobby": "hobby_agent",
            },
        )

        # 모든 에이전트 → merge → cascade → evaluate → END
        for agent_name in ["food_agent", "exercise_agent", "health_agent", "hobby_agent"]:
            graph.add_edge(agent_name, "merge_results")
        graph.add_edge("merge_results", "compute_cascade")
        graph.add_edge("compute_cascade", "evaluate")
        graph.add_edge("evaluate", END)

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

        # 대화 히스토리 로드
        history = self._memory.get(user_id, [])

        # LangGraph 실행
        initial_state: ChainState = {
            "user_id": user_id,
            "domain": domain,
            "action": action,
            "result": {},
            "cascade_effects": {},
            "affected_domains": [],
            "target_domains": [domain],
            "multi_results": {},
            "history": history[-10:],  # 최근 10턴
            "evaluation": {},
        }

        try:
            final_state = self._graph.invoke(initial_state)
        except Exception:
            logger.exception("LangGraph 실행 실패: user=%s, domain=%s", user_id, domain)
            final_state = {
                **initial_state,
                "result": {"recommendations": [], "explanation": "처리 중 오류가 발생했습니다."},
                "cascade_effects": {},
                "evaluation": {"has_result": False, "error": True},
            }

        # 히스토리 저장
        turn = {
            "domain": domain,
            "action": action,
            "result": final_state.get("result", {}),
        }
        if user_id not in self._memory:
            self._memory[user_id] = []
        self._memory[user_id].append(turn)
        # 메모리 상한 (50턴)
        if len(self._memory[user_id]) > 50:
            self._memory[user_id] = self._memory[user_id][-50:]

        return {
            "user_id": final_state["user_id"],
            "domain": final_state["domain"],
            "result": final_state["result"],
            "cascade_effects": final_state["cascade_effects"],
            "evaluation": final_state.get("evaluation", {}),
            "history_length": len(self._memory.get(user_id, [])),
        }

    # --- 인텐트 분류 ---

    def _classify_intent_node(self, state: ChainState) -> ChainState:
        """인텐트 분류 노드 — 쿼리에서 도메인 감지."""
        action = state["action"]
        query = action.get("query", "")

        if state["domain"] in self.VALID_DOMAINS:
            # 명시적 도메인이 이미 지정된 경우
            return {**state, "target_domains": [state["domain"]]}

        # 키워드 기반 멀티 도메인 감지
        detected = []
        for domain, keywords in DOMAIN_KEYWORDS.items():
            if any(kw in query for kw in keywords):
                detected.append(domain)

        if not detected:
            detected = ["food"]  # 기본값

        return {**state, "domain": detected[0], "target_domains": detected}

    def _route_to_agent(self, state: ChainState) -> str:
        """조건 분기 함수 — 도메인에 따라 에이전트 선택."""
        return state["domain"]

    # --- 에이전트 노드 ---

    def _food_agent_node(self, state: ChainState) -> ChainState:
        """음식 에이전트 노드."""
        result = self.food_agent.recommend(state["action"])
        return {**state, "result": result, "multi_results": {**state.get("multi_results", {}), "food": result}}

    def _exercise_agent_node(self, state: ChainState) -> ChainState:
        """운동 에이전트 노드."""
        result = self.exercise_agent.recommend(state["action"])
        return {**state, "result": result, "multi_results": {**state.get("multi_results", {}), "exercise": result}}

    def _health_agent_node(self, state: ChainState) -> ChainState:
        """건강 에이전트 노드."""
        result = self.health_agent.analyze_checkup(state["action"])
        return {**state, "result": result, "multi_results": {**state.get("multi_results", {}), "health": result}}

    def _hobby_agent_node(self, state: ChainState) -> ChainState:
        """취미 에이전트 노드."""
        result = self.hobby_agent.recommend(state["action"])
        return {**state, "result": result, "multi_results": {**state.get("multi_results", {}), "hobby": result}}

    # --- 후처리 노드 ---

    def _merge_results_node(self, state: ChainState) -> ChainState:
        """결과 병합 노드 — 멀티 도메인 결과 통합."""
        multi = state.get("multi_results", {})
        if len(multi) > 1:
            # 멀티 도메인: 결과를 통합
            return {**state, "result": {"multi_domain": True, "domains": multi}}
        return state

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

    def _evaluate_node(self, state: ChainState) -> ChainState:
        """평가 노드 — 결과 품질 메트릭 생성."""
        result = state.get("result", {})
        cascade = state.get("cascade_effects", {})

        evaluation = {
            "has_result": bool(result),
            "cascade_count": len(cascade.get("affected_domains", [])),
            "domains_involved": state.get("target_domains", []),
            "history_context_used": len(state.get("history", [])) > 0,
        }

        return {**state, "evaluation": evaluation}
