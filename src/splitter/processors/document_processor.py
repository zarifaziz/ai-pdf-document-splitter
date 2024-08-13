import random
import uuid
from typing import Dict, List

import numpy as np
from openai import OpenAI
from pydantic import BaseModel, Field

from ..domain_models import Document, PageInfo
from ..settings import settings

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)


class TopicName(BaseModel):
    topic_name: str = Field(..., description="The topic of the document")


def generate_topic(text: str) -> str:
    completion = openai_client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Generate a succint and specific legal domain topic for the given text in 1 to 2 words e.g. 'Cancellation', 'Medical_Documents', 'Court_Filings', 'Media Coverage'",
            },
            {"role": "user", "content": f"{text}"},
        ],
        response_format=TopicName,
    )
    return str(completion.choices[0].message.parsed.topic_name)


def generate_topic_dummy(text: str) -> str:
    return "Dummy Topic"


def create_documents(
    page_infos: List[PageInfo], clusters: np.ndarray
) -> Dict[int, Document]:
    documents = {}
    for page_info, cluster in zip(page_infos, clusters):
        if cluster not in documents:
            documents[cluster] = Document(
                id=str(uuid.uuid4()),
                topic_name=f"Cluster {cluster}",
                pages=[],
                page_range=(page_info.page_number, page_info.page_number),
            )
        documents[cluster].pages.append(page_info)
        documents[cluster].page_range = (
            min(documents[cluster].page_range[0], page_info.page_number),
            max(documents[cluster].page_range[1], page_info.page_number),
        )
    return documents


def assign_topics_to_documents(
    documents_dict: Dict[int, Document], texts: List[str], strategy: str = "first_page"
) -> Dict[int, Document]:
    for document in documents_dict.values():
        try:
            if strategy == "random_sample":
                # Randomly select up to 5 pages from each document
                selected_pages = random.sample(document.pages, min(5, len(document.pages)))
                page_texts = [texts[page.page_number] for page in selected_pages]
                combined_text = " ".join(page_texts)
                document.topic_name = generate_topic(combined_text)
            elif strategy == "first_page":
                # Select the first page from each document
                first_page = document.pages[0]
                page_text = texts[first_page.page_number]
                document.topic_name = generate_topic(page_text)
            else:
                raise ValueError(f"Unknown strategy: {strategy}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    return documents_dict
