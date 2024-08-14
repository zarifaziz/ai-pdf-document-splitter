import os
import pickle
from typing import List

import numpy as np
from openai import OpenAI

from ..settings import settings

from loguru import logger

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_embedding(text: str) -> np.ndarray:
    """Generate an embedding for a single text."""
    response = openai_client.embeddings.create(
        input=text, model="text-embedding-3-small"
    )
    return np.array(response.data[0].embedding)


def generate_embeddings(input_file: str, texts: List[str]) -> List[np.ndarray]:
    """Generate embeddings for a list of texts, or load from file if it exists."""
    input_file_name = os.path.basename(input_file)
    input_file_name_without_ext = os.path.splitext(input_file_name)[0]
    embeddings_file_path = f"data/{input_file_name_without_ext}_{settings.EMBEDDINGS_FILE_SUFFIX}"

    if os.path.exists(embeddings_file_path):
        logger.info(f"Loading existing embeddings from {embeddings_file_path}")
        with open(embeddings_file_path, "rb") as f:
            return pickle.load(f)

    logger.info(f"Creating new embeddings for {input_file_name}")
    response = openai_client.embeddings.create(
        input=texts, model="text-embedding-3-small"
    )
    embeddings = [np.array(embedding.embedding) for embedding in response.data]

    with open(embeddings_file_path, "wb") as f:
        pickle.dump(embeddings, f)

    return embeddings


def save_embeddings(input_file: str, embeddings: List) -> None:
    """Save embeddings to a file if it doesn't already exist."""
    input_file_name = os.path.basename(input_file)
    input_file_name_without_ext = os.path.splitext(input_file_name)[0]
    embeddings_file_path = f"data/{input_file_name_without_ext}_{settings.EMBEDDINGS_FILE_SUFFIX}"
    
    if os.path.exists(embeddings_file_path):
        logger.info(f"Embeddings file {embeddings_file_path} already exists. Skipping save.")
        return
    
    with open(embeddings_file_path, "wb") as f:
        pickle.dump(embeddings, f)


def load_embeddings(input_file: str) -> List:
    """Load embeddings from a file."""
    input_file_name = os.path.basename(input_file)
    input_file_name_without_ext = os.path.splitext(input_file_name)[0]
    embeddings_file_path = f"data/{input_file_name_without_ext}_{settings.EMBEDDINGS_FILE_SUFFIX}"

    with open(embeddings_file_path, "rb") as f:
        return pickle.load(f)
