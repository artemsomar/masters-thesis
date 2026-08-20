from collections.abc import AsyncIterator

from app.modules.analysis.schemas import AnalysisAnswer, AnalysisResult
from app.modules.diagrams.schemas import Diagram, DiagramGenerationRequest
from app.modules.sessions.models import DiagramSession
from app.modules.sessions.schemas import SessionStatusUpdate


class FakeSessionRepository:
    def __init__(self) -> None:
        self.sessions: dict[str, DiagramSession] = {}

    async def get(self, session_id: str) -> DiagramSession | None:
        return self.sessions.get(session_id)

    async def save(self, session: DiagramSession) -> None:
        self.sessions[session.id] = session

    async def delete(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)


class FakeSessionEventBroker:
    def __init__(self) -> None:
        self.events: dict[str, list[SessionStatusUpdate]] = {}

    async def publish_status(self, session_id: str, event: SessionStatusUpdate) -> None:
        self.events.setdefault(session_id, []).append(event)

    async def subscribe_statuses(
        self, session_id: str
    ) -> AsyncIterator[SessionStatusUpdate | None]:
        for event in self.events.get(session_id, []):
            yield event


class FakeSessionCreationLimiter:
    def __init__(self) -> None:
        self.acquired: set[str] = set()

    async def acquire(self, session_id: str, client_fingerprint: str) -> None:
        self.acquired.add(session_id)

    async def release(self, session_id: str) -> None:
        self.acquired.discard(session_id)


class FakeSessionJobDispatcher:
    def __init__(self) -> None:
        self.dispatched: list[tuple[str, str]] = []
        self.cancelled: list[str] = []

    def dispatch_session_processing(self, session_id: str, job_id: str) -> None:
        self.dispatched.append((session_id, job_id))

    def cancel(self, job_id: str) -> None:
        self.cancelled.append(job_id)


class FakeRequirementsAnalyzer:
    def __init__(self, result: AnalysisResult) -> None:
        self._result = result
        self.calls: list[tuple[str, str, list[AnalysisAnswer], bool]] = []

    async def analyze(
        self,
        description: str,
        language: str,
        answers: list[AnalysisAnswer],
        allow_questions: bool,
    ) -> AnalysisResult:
        self.calls.append((description, language, answers, allow_questions))
        return self._result


class FakeDiagramGenerator:
    def __init__(self, result: Diagram | Exception) -> None:
        self._result = result
        self.calls: list[DiagramGenerationRequest] = []

    async def generate(self, request: DiagramGenerationRequest) -> Diagram:
        self.calls.append(request)
        if isinstance(self._result, Exception):
            raise self._result
        return self._result
