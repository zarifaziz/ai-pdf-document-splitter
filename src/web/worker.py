import os
import redis
from rq import Connection, Queue, Worker
from src.splitter.pipeline import Pipeline

# Connect to Redis
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_conn = redis.from_url(redis_url)

# Define the queue
queue = Queue(connection=redis_conn)

def run_pipeline(file_key, distance_threshold):
    # Retrieve the file from Redis
    file_content = redis_conn.get(file_key)
    if file_content is None:
        raise FileNotFoundError(f"File not found in Redis: {file_key}")

    # Save the file to a temporary location
    local_file_path = os.path.join("data/input_pdf", os.path.basename(file_key))
    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
    with open(local_file_path, "wb") as f:
        f.write(file_content)

    # Run the pipeline
    pipeline = Pipeline(local_file_path, distance_threshold)
    output_files = pipeline.run()

    # Delete the file from Redis after successful run
    redis_conn.delete(file_key)
    
    return output_files

if __name__ == "__main__":
    with Connection(redis_conn):
        worker = Worker([queue])
        worker.work()