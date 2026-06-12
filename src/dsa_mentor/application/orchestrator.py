from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from dsa_mentor.agents.registry import AgentRegistry
from dsa_mentor.application.ports import KnowledgeRetriever
from dsa_mentor.application.problem_resolver import ProblemResolver
from dsa_mentor.application.routing import route_message
from dsa_mentor.domain.models import CodingProblem, MentorMode

SPECIALIST_MODES = (
    MentorMode.TUTOR,
    MentorMode.HINT,
    MentorMode.REVIEW,
    MentorMode.INTERVIEW,
    MentorMode.PATTERN_MAPPER,
    MentorMode.VISUALIZER,
)



class MentorState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    selected_mode: str
    model_id: str
    route: MentorMode
    problem: dict
    context: str
    response: str


class MentorOrchestrator:
    """Coordinates problem resolution, retrieval, routing, and one specialist agent."""

    def __init__(
        self,
        problem_resolver: ProblemResolver,
        retriever: KnowledgeRetriever,
        agents: AgentRegistry,
    ):
        self.problem_resolver = problem_resolver
        self.retriever = retriever
        self.agents = agents

    def compile(self):
        graph = StateGraph(MentorState)
        graph.add_node("resolve_problem", self._resolve_problem)
        graph.add_node("route", self._route)
        graph.add_node("retrieve", self._retrieve)
        for mode in SPECIALIST_MODES:
            graph.add_node(mode.value, self._specialist(mode))

        graph.add_edge(START, "resolve_problem")
        graph.add_edge("resolve_problem", "route")
        graph.add_edge("route", "retrieve")
        graph.add_conditional_edges(
            "retrieve",
            lambda state: state["route"].value,
            {mode.value: mode.value for mode in SPECIALIST_MODES},
        )
        for mode in SPECIALIST_MODES:
            graph.add_edge(mode.value, END)
        return graph.compile()

    def _resolve_problem(self, state: MentorState) -> MentorState:
        try:
            problem = self.problem_resolver.resolve(str(state["messages"][-1].content))
        except Exception:
            problem = None
        return {"problem": problem.model_dump()} if problem else {}

    def _route(self, state: MentorState) -> MentorState:
        return {
            "route": route_message(
                str(state["messages"][-1].content),
                state.get("selected_mode", MentorMode.AUTO.value),
            )
        }

    def _retrieve(self, state: MentorState) -> MentorState:
        problem = CodingProblem.model_validate(state["problem"]) if state.get("problem") else None
        query = problem.statement if problem else str(state["messages"][-1].content)
        try:
            return {"context": self.retriever.search(query)}
        except Exception:
            return {"context": ""}

    def _specialist(self, mode: MentorMode):
        def run(state: MentorState) -> MentorState:
            problem = CodingProblem.model_validate(state["problem"]) if state.get("problem") else None
            prompt = self.agents.system_prompt(mode, problem, state.get("context", ""))
            model = self.agents.model(state["model_id"])
            answer = model.invoke([SystemMessage(content=prompt), *state["messages"]])
            response = str(answer.content)
            return {"response": response, "messages": [AIMessage(content=response)]}

        return run
