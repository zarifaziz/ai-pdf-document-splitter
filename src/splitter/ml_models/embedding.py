import pickle
from typing import List

import numpy as np
from openai import OpenAI

from ..settings import settings

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_embedding(text: str) -> np.ndarray:
    """Generate an embedding for a single text."""
    response = openai_client.embeddings.create(
        input=text, model="text-embedding-3-small"
    )
    return np.array(response.data[0].embedding)


def generate_embeddings(texts: List[str]) -> List[np.ndarray]:
    """Generate embeddings for a list of texts."""
    response = openai_client.embeddings.create(
        input=texts, model="text-embedding-3-small"
    )
    return [np.array(embedding.embedding) for embedding in response.data]


def save_embeddings(embeddings: List) -> None:
    """Save embeddings to a file."""
    with open(settings.EMBEDDINGS_FILE, "wb") as f:
        pickle.dump(embeddings, f)


def load_embeddings() -> List:
    """Load embeddings from a file."""
    with open(settings.EMBEDDINGS_FILE, "rb") as f:
        return pickle.load(f)
