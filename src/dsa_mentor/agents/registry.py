from functools import lru_cache
from pathlib import Path

from langchain_groq import ChatGroq

from dsa_mentor.domain.models import CodingProblem, MentorMode
from dsa_mentor.infrastructure.config import Settings

PROMPT_ROOT = Path(__file__).resolve().parent / "prompts"


class AgentRegistry:
    def __init__(self, settings: Settings):
        self.settings = settings

    def model(self, model_id: str) -> ChatGroq:
        if model_id not in self.settings.groq_models:
            raise ValueError(f"Unsupported model: {model_id}")
        return ChatGroq(
            api_key=self.settings.groq_api_key,
            model=model_id,
            temperature=0.2,
        )

    @lru_cache
    def base_prompt(self, mode: MentorMode) -> str:
        return (PROMPT_ROOT / f"{mode.value}.md").read_text(encoding="utf-8")

    def system_prompt(
        self,
        mode: MentorMode,
        problem: CodingProblem | None,
        context: str,
    ) -> str:
        sections = [self.base_prompt(mode)]
        if problem:
            sections.append(
                "Resolved problem:\n"
                f"Title: {problem.title}\n"
                f"Difficulty: {problem.difficulty or 'unknown'}\n"
                f"Topics: {', '.join(problem.topics)}\n"
                f"Statement:\n{problem.statement}"
            )
        if context:
            sections.append(f"Relevant knowledge:\n{context}")
        return "\n\n".join(sections)
