import os
from multiprocessing import Pool
from typing import List

from openai import OpenAI

from .pdf_splitter import PdfSplitter
from .settings import settings
from .text_extractor import TextExtractor

from sklearn.cluster import AgglomerativeClustering
import numpy as np
from pydantic import BaseModel

import numpy as np
from typing import List, Tuple

class Pipeline:
    def __init__(self, input_file: str) -> None:
        self.input_file = input_file
        self.splitter = PdfSplitter(input_file)
        self.text_extractor = TextExtractor()
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_embedding(self, text: str) -> np.ndarray:
        response = self.openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return np.array(response.data[0].embedding)

    def generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        response = self.openai_client.embeddings.create(
            input=texts,
            model="text-embedding-3-small"
        )
        return [np.array(embedding.embedding) for embedding in response.data]

    def run(self) -> None:
        os.makedirs(settings.PDF_OUTPUT_DIR, exist_ok=True)
        os.makedirs(settings.TXT_OUTPUT_DIR, exist_ok=True)
        
        self.splitter.run()
        pdf_files: List[str] = [
            os.path.join(settings.PDF_OUTPUT_DIR, f)
            for f in os.listdir(settings.PDF_OUTPUT_DIR)
            if f.endswith(".pdf")
        ]
        with Pool() as pool:
            pool.starmap(TextExtractor.convert_pdf_to_text, [(pdf_file,) for pdf_file in pdf_files])
        
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

        # Perform agglomerative clustering
        embeddings = np.array(embeddings)
        clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=1.5)
        clusters = clustering.fit_predict(embeddings)

        # Print or store the clustering results
        for text_file, cluster in zip(text_files, clusters):
            print(f"{text_file} -> Cluster {cluster}")


if __name__ == "__main__":
    pipeline = Pipeline("data/input_pdf/take_home_challenge.pdf")
    pipeline.run()
