from dsa_mentor.domain.models import ProblemReference, ProblemReferenceKind
from dsa_mentor.infrastructure.problem_sources.leetcode import LeetCodeProblemSource


def test_resolves_number_then_loads_problem(monkeypatch) -> None:
    source = LeetCodeProblemSource()
    replies = iter(
        [
            {
                "data": {
                    "problemsetQuestionList": {
                        "questions": [
                            {
                                "frontendQuestionId": "1",
                                "title": "Two Sum",
                                "titleSlug": "two-sum",
                                "difficulty": "Easy",
                            }
                        ]
                    }
                }
            },
            {
                "data": {
                    "question": {
                        "questionFrontendId": "1",
                        "title": "Two Sum",
                        "titleSlug": "two-sum",
                        "difficulty": "Easy",
                        "content": "<p>Find two values.</p>",
                        "topicTags": [{"name": "Array", "slug": "array"}],
                    }
                }
            },
        ]
    )
    monkeypatch.setattr(source, "_post", lambda *args, **kwargs: next(replies))

    problem = source.resolve(ProblemReference(kind=ProblemReferenceKind.NUMBER, value="1"))

    assert problem
    assert problem.title == "Two Sum"
    assert problem.statement == "Find two values."
    assert problem.topics == ["Array"]
