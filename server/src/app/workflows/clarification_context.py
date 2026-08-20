from app.modules.sessions.schemas import ClarificationHistoryEntry


def build_clarification_context(entries: list[ClarificationHistoryEntry]) -> str:
    if not entries:
        return "No clarification history."
    return "\n\n".join(
        f"### Round {entry.round}\n\nQuestion: {entry.question}\n\nAnswer: {entry.answer}"
        for entry in entries
    )
