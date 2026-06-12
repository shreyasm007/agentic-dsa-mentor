from dsa_mentor.agents.registry import AgentRegistry
from dsa_mentor.application.orchestrator import MentorOrchestrator
from dsa_mentor.application.problem_resolver import ProblemResolver
from dsa_mentor.infrastructure.config import Settings, get_settings
from dsa_mentor.infrastructure.problem_sources.leetcode import LeetCodeProblemSource
from dsa_mentor.infrastructure.retrieval.qdrant_voyage import (
    NullKnowledgeRetriever,
    QdrantVoyageRetriever,
)


def build_orchestrator(settings: Settings | None = None):
    settings = settings or get_settings()
    retriever = (
        QdrantVoyageRetriever(settings)
        if settings.voyage_api_key
        else NullKnowledgeRetriever()
    )
    return MentorOrchestrator(
        problem_resolver=ProblemResolver(LeetCodeProblemSource()),
        retriever=retriever,
        agents=AgentRegistry(settings),
    ).compile()
