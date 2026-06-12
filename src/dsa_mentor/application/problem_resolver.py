import re

from dsa_mentor.application.ports import ProblemSource
from dsa_mentor.domain.models import (
    CodingProblem,
    ProblemReference,
    ProblemReferenceKind,
)

LEETCODE_URL = re.compile(r"https?://(?:www\.)?leetcode\.com/problems/([^/\s?#]+)")
LEETCODE_NUMBER = re.compile(r"\b(?:leetcode|lc)\s*(?:#|number|no\.?)?\s*(\d+)\b", re.I)
LEETCODE_TITLE = re.compile(r"\b(?:leetcode|lc)\s*[:#-]?\s*([a-z][a-z0-9 -]{2,60})", re.I)


class ProblemResolver:
    """Dedicated agent boundary for recognizing and loading coding problems."""

    def __init__(self, source: ProblemSource):
        self.source = source

    def identify(self, message: str) -> ProblemReference:
        if match := LEETCODE_URL.search(message):
            return ProblemReference(kind=ProblemReferenceKind.URL, value=match.group(1))
        if match := LEETCODE_NUMBER.search(message):
            return ProblemReference(kind=ProblemReferenceKind.NUMBER, value=match.group(1))
        if match := LEETCODE_TITLE.search(message):
            title = match.group(1).strip().lower()
            slug = re.sub(r"[^a-z0-9]+", "-", title).strip("-")
            return ProblemReference(kind=ProblemReferenceKind.SLUG, value=slug)
        if len(message) > 450 and any(
            marker in message.lower() for marker in ("input:", "output:", "constraints:")
        ):
            return ProblemReference(kind=ProblemReferenceKind.PASTED, value=message)
        return ProblemReference(kind=ProblemReferenceKind.NONE)

    def resolve(self, message: str) -> CodingProblem | None:
        reference = self.identify(message)
        if reference.kind == ProblemReferenceKind.PASTED:
            return CodingProblem(title="User-provided problem", statement=reference.value)
        if reference.kind == ProblemReferenceKind.NONE:
            return None
        return self.source.resolve(reference)
