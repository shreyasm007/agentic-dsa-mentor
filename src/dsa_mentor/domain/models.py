from enum import StrEnum

from pydantic import BaseModel, Field


class MentorMode(StrEnum):
    AUTO = "auto"
    TUTOR = "tutor"
    HINT = "hint"
    REVIEW = "review"
    INTERVIEW = "interview"
    PATTERN_MAPPER = "pattern_mapper"
    VISUALIZER = "visualizer"



class ProblemReferenceKind(StrEnum):
    URL = "url"
    NUMBER = "number"
    SLUG = "slug"
    PASTED = "pasted"
    NONE = "none"


class ProblemReference(BaseModel):
    kind: ProblemReferenceKind
    value: str = ""


class CodingProblem(BaseModel):
    source: str = "user"
    frontend_id: str | None = None
    title: str
    slug: str | None = None
    difficulty: str | None = None
    statement: str
    examples: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    url: str | None = None
