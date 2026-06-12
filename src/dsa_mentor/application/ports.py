from typing import Protocol

from dsa_mentor.domain.models import CodingProblem, ProblemReference


class ProblemSource(Protocol):
    def resolve(self, reference: ProblemReference) -> CodingProblem | None: ...


class KnowledgeRetriever(Protocol):
    def search(self, query: str, limit: int = 4) -> str: ...
