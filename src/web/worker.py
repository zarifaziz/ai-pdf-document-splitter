import os
import redis
from rq import Connection, Queue, Worker
from src.splitter.pipeline import Pipeline
from loguru import logger

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
    sanitized_file_key = file_key.replace("pdf:", "")
    local_file_path = os.path.join("data/input_pdf", os.path.basename(sanitized_file_key))
    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
    with open(local_file_path, "wb") as f:
        f.write(file_content)

    # Run the pipeline
    pipeline = Pipeline(local_file_path, distance_threshold)
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

    # Delete the file from Redis after successful run
    redis_conn.delete(file_key)
    
    return output_files

if __name__ == "__main__":
    with Connection(redis_conn):
        worker = Worker([queue])
        worker.work()