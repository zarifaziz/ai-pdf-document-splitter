import os

import redis
from loguru import logger
from rq import Connection, Queue, Worker

from src.splitter.pipeline import Pipeline

# Connect to Redis
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_conn = redis.from_url(redis_url)

# Define the queue
queue = Queue(connection=redis_conn)


def run_pipeline(temp_file_path, distance_threshold):
    if not os.path.exists(temp_file_path):
        raise FileNotFoundError(f"File not found: {temp_file_path}")

    pipeline = Pipeline(temp_file_path, distance_threshold)
    try:
        output_files = pipeline.run()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        logger.error(f"logging contents of data/ dir below:\n")
        # Log the contents of the data directory
        data_directory = "data"
        if os.path.exists(data_directory):
            for root, dirs, files in os.walk(data_directory):
                for name in files:
                    logger.info(f"File: {os.path.join(root, name)}")
                for name in dirs:
                    logger.info(f"Directory: {os.path.join(root, name)}")
        raise

    return output_files


if __name__ == "__main__":
    with Connection(redis_conn):
        worker = Worker([queue])
        worker.work()
