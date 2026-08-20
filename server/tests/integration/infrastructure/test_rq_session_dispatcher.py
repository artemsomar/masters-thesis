import os
from uuid import uuid4

import pytest
from redis import Redis
from rq import Queue

from app.infrastructure.queue.rq_session_dispatcher import RqSessionJobDispatcher

_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/15")


@pytest.mark.integration
def test_rq_dispatcher_enqueues_a_session_job() -> None:
    connection = Redis.from_url(_REDIS_URL)
    try:
        connection.ping()
    except Exception:
        connection.close()
        pytest.skip("Redis is required for integration tests")

    job_id = str(uuid4())
    queue = Queue("test-diagram-jobs", connection=connection)
    dispatcher = RqSessionJobDispatcher(connection, queue.name, 120, 3, [10, 20])
    dispatcher.dispatch_session_processing("session-id", job_id)

    job = queue.fetch_job(job_id)
    assert job is not None
    assert job.args == ("session-id",)

    dispatcher.cancel(job_id)
    job.delete()
    connection.close()
