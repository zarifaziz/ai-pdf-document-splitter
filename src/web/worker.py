import os

import redis
from rq import Connection, Queue, Worker

from src.splitter.pipeline import Pipeline

# Connect to Redis
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_conn = redis.from_url(redis_url)

# Define the queue
queue = Queue(connection=redis_conn)


def run_pipeline(temp_file_path, distance_threshold):
    pipeline = Pipeline(temp_file_path, distance_threshold)
    output_files = pipeline.run()
    return output_files


if __name__ == "__main__":
    with Connection(redis_conn):
        worker = Worker([queue])
        worker.work()
