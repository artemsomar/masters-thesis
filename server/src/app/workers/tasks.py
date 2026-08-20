import asyncio

from app.bootstrap import build_container


def process_session(session_id: str) -> None:
    container = build_container()
    asyncio.run(container.diagram_session_workflow.process_session(session_id))
