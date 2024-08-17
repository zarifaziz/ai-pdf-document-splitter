import os
import redis
from rq import Worker, Queue, Connection
from src.splitter.pipeline import Pipeline

# Connect to Redis
redis_conn = redis.Redis(host='localhost', port=6379)

# Define the queue
queue = Queue(connection=redis_conn)

def run_pipeline(temp_file_path):
    pipeline = Pipeline(temp_file_path)
    output_files = pipeline.run()
    return output_files

if __name__ == '__main__':
    with Connection(redis_conn):
        worker = Worker([queue])
        worker.work()