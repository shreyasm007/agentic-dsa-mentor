import pytest

from dsa_mentor.application.routing import route_message
from dsa_mentor.domain.models import MentorMode


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Give me a hint for LeetCode 3", MentorMode.HINT),
        ("Review my code", MentorMode.REVIEW),
        ("Run a mock interview", MentorMode.INTERVIEW),
        ("What pattern is this?", MentorMode.PATTERN_MAPPER),
        ("Explain dynamic programming", MentorMode.TUTOR),
    ],
)
def test_route_message(message: str, expected: MentorMode) -> None:
    assert route_message(message) == expected


def test_explicit_mode_wins() -> None:
    assert route_message("Explain BFS", MentorMode.INTERVIEW.value) == MentorMode.INTERVIEW
