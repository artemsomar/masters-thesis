from redis import Redis
from rq import Queue, Worker

from app.bootstrap import build_container


def run() -> None:
    container = build_container()
    connection = Redis.from_url(str(container.settings.redis_url))
    queue = Queue(container.settings.rq_queue_name, connection=connection)
    Worker([queue], connection=connection).work()


if __name__ == "__main__":
    run()
