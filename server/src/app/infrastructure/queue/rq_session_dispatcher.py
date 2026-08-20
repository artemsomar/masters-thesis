from redis import Redis
from rq import Queue, Retry
from rq.job import Job
from rq.exceptions import NoSuchJobError

from app.logging_config import get_correlation_id


class RqSessionJobDispatcher:
    def __init__(
        self,
        connection: Redis,
        queue_name: str,
        job_timeout_seconds: int,
        max_attempts: int,
        retry_intervals_seconds: list[int],
    ) -> None:
        self._queue = Queue(queue_name, connection=connection)
        self._connection = connection
        self._job_timeout_seconds = job_timeout_seconds
        self._max_attempts = max_attempts
        self._retry_intervals_seconds = retry_intervals_seconds

    def dispatch_session_processing(self, session_id: str, job_id: str) -> None:
        self._queue.enqueue(
            "app.workers.tasks.process_session",
            session_id,
            job_id=job_id,
            job_timeout=self._job_timeout_seconds,
            retry=Retry(
                max=self._max_attempts - 1,
                interval=self._retry_intervals_seconds[: self._max_attempts - 1],
            ),
            on_failure="app.workers.tasks.mark_session_processing_failed",
            meta={"correlation_id": get_correlation_id()},
        )

    def cancel(self, job_id: str) -> None:
        try:
            Job.fetch(job_id, connection=self._connection).cancel()
        except NoSuchJobError:
            return
