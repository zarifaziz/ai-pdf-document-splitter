import os
import uuid
from multiprocessing import Pool
from typing import List, Tuple

import numpy as np
from openai import OpenAI
from pydantic import BaseModel, Field
from sklearn.cluster import AgglomerativeClustering

from .models import Document, PageInfo
from .pdf_merger import PdfMerger
from .pdf_splitter import PdfSplitter
from .settings import settings
from .text_extractor import TextExtractor

class TopicName(BaseModel):
    topic_name: str = Field(..., description="The topic of the document")

class Pipeline:
    def __init__(self, input_file: str) -> None:
        self.input_file = input_file
        self.splitter = PdfSplitter(input_file)
        self.text_extractor = TextExtractor()
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_embedding(self, text: str) -> np.ndarray:
        response = self.openai_client.embeddings.create(
            input=text, model="text-embedding-3-small"
        )
        return np.array(response.data[0].embedding)

    def generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        response = self.openai_client.embeddings.create(
            input=texts, model="text-embedding-3-small"
        )
        return [np.array(embedding.embedding) for embedding in response.data]

    class TopicName(BaseModel):
        topic_name: str = Field(..., description="The topic of the document")

    def generate_topic(self, text: str) -> str:
        completion = self.openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Generate a succint topic for the given text in 1 to 2 words e.g. 'Correspondence', 'Medical Documents', 'Court Filings'",
                },
                {"role": "user", "content": f"{text}"},
            ],
            response_format=TopicName,
        )
        return str(completion.choices[0].message.parsed.topic_name)

    def run(self) -> None:
        os.makedirs(settings.TEMP_PDF_PAGES_DIR, exist_ok=True)
        os.makedirs(settings.TXT_OUTPUT_DIR, exist_ok=True)
        os.makedirs(settings.OUTPUT_DOCS_DIR, exist_ok=True)

        self.splitter.run()
        pdf_files: List[str] = [
            os.path.join(settings.TEMP_PDF_PAGES_DIR, f)
            for f in os.listdir(settings.TEMP_PDF_PAGES_DIR)
            if f.endswith(".pdf")
        ]
        with Pool() as pool:
            pool.starmap(
                TextExtractor.convert_pdf_to_text,
                [(pdf_file,) for pdf_file in pdf_files],
            )

        text_files = [
            os.path.join(settings.TXT_OUTPUT_DIR, f)
            for f in os.listdir(settings.TXT_OUTPUT_DIR)
            if f.endswith(".txt")
        ]
        texts = []
        for text_file in text_files:
            with open(text_file, "r") as file:
                texts.append(file.read())

        embeddings = self.generate_embeddings(texts)

        # Create PageInfo objects
        page_infos = [
            PageInfo(input_pdf_path=self.input_file, page_number=i, embedding=embedding)
            for i, embedding in enumerate(embeddings)
        ]

        # Perform agglomerative clustering
        embeddings_array = np.array(embeddings)
        clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=1.5)
        clusters = clustering.fit_predict(embeddings_array)

        # Create Document objects based on clusters
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

        # Generate topics for each document
        for document in documents.values():
            first_page_text = texts[document.pages[0].page_number]
            document.topic_name = self.generate_topic(first_page_text)

        # Output the clustering results
        for document in documents.values():
            print(
                f"Document ID: {document.id}, Topic: {document.topic_name}, Page Range: {document.page_range}"
            )
            for page in document.pages:
                print(f"  Page {page.page_number} from {page.input_pdf_path}")

        # Create individual PDF documents based on the clusters
        pdf_merger = PdfMerger(self.input_file)
        for id, document in documents.items():
            output_file = os.path.join(
                settings.OUTPUT_DOCS_DIR, f"document_{id}_{document.topic_name}.pdf"
            )
            page_numbers = [page.page_number for page in document.pages]
            pdf_merger.merge_pages(page_numbers, output_file)


if __name__ == "__main__":
    pipeline = Pipeline("data/input_pdf/take_home_challenge.pdf")
    pipeline.run()
