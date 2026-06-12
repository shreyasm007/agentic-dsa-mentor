from dsa_mentor.application.problem_resolver import ProblemResolver
from dsa_mentor.domain.models import CodingProblem, ProblemReferenceKind


class FakeSource:
    def resolve(self, reference):
        return CodingProblem(title=reference.value, statement="Loaded")


def test_identifies_leetcode_url() -> None:
    resolver = ProblemResolver(FakeSource())
    reference = resolver.identify("Help with https://leetcode.com/problems/two-sum/")
    assert reference.kind == ProblemReferenceKind.URL
    assert reference.value == "two-sum"


def test_identifies_leetcode_number() -> None:
    resolver = ProblemResolver(FakeSource())
    reference = resolver.identify("Give me a hint for LeetCode #42")
    assert reference.kind == ProblemReferenceKind.NUMBER
    assert reference.value == "42"


def test_identifies_explicit_leetcode_title() -> None:
    resolver = ProblemResolver(FakeSource())
    reference = resolver.identify("LeetCode: Longest Substring Without Repeating Characters")
    assert reference.kind == ProblemReferenceKind.SLUG
    assert reference.value == "longest-substring-without-repeating-characters"


def test_resolves_pasted_problem_without_external_source() -> None:
    resolver = ProblemResolver(FakeSource())
    text = "Given an array..." * 40 + "\nInput: [1]\nOutput: 1\nConstraints: n > 0"
    problem = resolver.resolve(text)
    assert problem
    assert problem.source == "user"
