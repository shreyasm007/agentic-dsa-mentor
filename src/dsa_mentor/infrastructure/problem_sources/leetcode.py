import httpx
from bs4 import BeautifulSoup

from dsa_mentor.domain.models import CodingProblem, ProblemReference, ProblemReferenceKind

LEETCODE_GRAPHQL = "https://leetcode.com/graphql"

LIST_QUERY = """
query problemsetQuestionList($filters: QuestionListFilterInput) {
  problemsetQuestionList(categorySlug: "", limit: 20, skip: 0, filters: $filters) {
    questions { frontendQuestionId title titleSlug difficulty }
  }
}
"""

DETAIL_QUERY = """
query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionFrontendId title titleSlug difficulty content
    topicTags { name slug }
  }
}
"""


class LeetCodeProblemSource:
    """Reads public problem metadata through LeetCode's web GraphQL endpoint."""

    def __init__(self, timeout: float = 12.0):
        self.timeout = timeout

    def resolve(self, reference: ProblemReference) -> CodingProblem | None:
        slug = reference.value
        if reference.kind == ProblemReferenceKind.NUMBER:
            slug = self._find_slug_by_number(reference.value)
        if not slug:
            return None
        return self._fetch_by_slug(slug)

    def _find_slug_by_number(self, frontend_id: str) -> str | None:
        payload = self._post(
            LIST_QUERY,
            {"filters": {"searchKeywords": frontend_id}},
            operation_name="problemsetQuestionList",
        )
        questions = payload.get("data", {}).get("problemsetQuestionList", {}).get("questions", [])
        exact = next(
            (question for question in questions if question["frontendQuestionId"] == frontend_id),
            None,
        )
        return exact["titleSlug"] if exact else None

    def _fetch_by_slug(self, slug: str) -> CodingProblem | None:
        payload = self._post(
            DETAIL_QUERY,
            {"titleSlug": slug},
            operation_name="questionData",
        )
        question = payload.get("data", {}).get("question")
        if not question:
            return None
        text = BeautifulSoup(question["content"] or "", "html.parser").get_text("\n", strip=True)
        return CodingProblem(
            source="leetcode",
            frontend_id=question["questionFrontendId"],
            title=question["title"],
            slug=question["titleSlug"],
            difficulty=question["difficulty"],
            statement=text,
            topics=[topic["name"] for topic in question["topicTags"]],
            url=f"https://leetcode.com/problems/{question['titleSlug']}/",
        )

    def _post(self, query: str, variables: dict, operation_name: str) -> dict:
        response = httpx.post(
            LEETCODE_GRAPHQL,
            json={"query": query, "variables": variables, "operationName": operation_name},
            headers={"User-Agent": "agentic-dsa-mentor/0.1"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
