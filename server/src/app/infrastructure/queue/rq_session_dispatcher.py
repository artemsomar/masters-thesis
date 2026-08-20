from redis import Redis
from rq import Queue
from rq.job import Job
from rq.exceptions import NoSuchJobError


class RqSessionJobDispatcher:
    def __init__(self, connection: Redis, queue_name: str) -> None:
        self._queue = Queue(queue_name, connection=connection)
        self._connection = connection

    def dispatch_session_processing(self, session_id: str, job_id: str) -> None:
        self._queue.enqueue(
            "app.workers.tasks.process_session",
            session_id,
            job_id=job_id,
            job_timeout=60,
        )

    def cancel(self, job_id: str) -> None:
        try:
            Job.fetch(job_id, connection=self._connection).cancel()
        except NoSuchJobError:
            return
