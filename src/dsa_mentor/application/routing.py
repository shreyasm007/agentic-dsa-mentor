from dsa_mentor.domain.models import MentorMode


def route_message(message: str, selected_mode: str = "auto") -> MentorMode:
    if selected_mode != MentorMode.AUTO:
        return MentorMode(selected_mode)

    text = message.lower()
    rules = [
        (MentorMode.INTERVIEW, ("mock interview", "be the interviewer", "interview simulation")),
        (MentorMode.HINT, ("hint", "i'm stuck", "im stuck", "don't tell me", "guidance")),
        (
            MentorMode.REVIEW,
            ("review my code", "review this code", "is this optimal", "wrong with my solution"),
        ),
        (
            MentorMode.PATTERN_MAPPER,
            ("what pattern", "which pattern", "which technique", "similar problems"),
        ),
        (MentorMode.TUTOR, ("explain", "teach me", "what is", "how does", "don't understand")),
    ]
    for mode, phrases in rules:
        if any(phrase in text for phrase in phrases):
            return mode
    return MentorMode.TUTOR
