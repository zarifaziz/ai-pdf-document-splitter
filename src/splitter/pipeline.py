import os
import shutil
from typing import Dict, List

from .domain_models import Document, PageInfo
from .ml_models.clustering import perform_clustering
from .ml_models.embedding import (generate_embeddings, load_embeddings,
                                  save_embeddings)
from .processors.document_processor import (assign_topics_to_documents,
                                            create_documents)
from .processors.pdf_processor import PDFMerger
from .processors.text_extractor import TextExtractor
from .settings import settings


class Pipeline:
    def __init__(self, input_file: str) -> None:
        """Initialize the Pipeline with the input file and text extractor."""
        self.input_file = input_file
        self.text_extractor = TextExtractor()

    def run(self, clear_cache: bool = False) -> None:
        """Execute the entire pipeline process."""
        if clear_cache:
            self.clear_cache()

        # self.text_extractor.extract_texts_from_pdfs(self.input_file)
        texts = self.text_extractor.read_extracted_texts()
        # embeddings = generate_embeddings(texts)
        # save_embeddings(embeddings)
        embeddings = load_embeddings()
        page_infos = self.create_page_infos(embeddings)
        clusters = perform_clustering(embeddings)
        documents = create_documents(page_infos, clusters)

        documents = assign_topics_to_documents(documents, texts)

        self.output_clustering_results(documents)
        self.create_pdf_documents(documents)

    def clear_cache(self) -> None:
        """Clear the temporary and output directories."""
        directories_to_clear = [
            settings.TEMP_PDF_PAGES_DIR,
            settings.TEMP_IMAGE_DIR,
            settings.TXT_OUTPUT_DIR,
            settings.OUTPUT_DOCS_DIR,
        ]
        for directory in directories_to_clear:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")

    def output_clustering_results(self, documents_dict: Dict[int, Document]) -> None:
        """Print the clustering results for each document."""
        for document in documents_dict.values():
            print(
                f"Document ID: {document.id}, Topic: {document.topic_name}, Page Range: {document.page_range}"
            )

    def create_pdf_documents(self, documents: Dict[int, Document]) -> None:
        """Create PDF documents from the clustered pages."""
        pdf_merger = PDFMerger(self.input_file)
        for id, document in documents.items():
            output_file = os.path.join(
                settings.OUTPUT_DOCS_DIR, f"document_{id}_{document.topic_name}.pdf"
            )
            page_numbers = [page.page_number for page in document.pages]
            pdf_merger.merge_pages(page_numbers, output_file)

    def create_page_infos(self, embeddings: List) -> List[PageInfo]:
        """Create PageInfo objects from the embeddings."""
        return [
            PageInfo(input_pdf_path=self.input_file, page_number=i, embedding=embedding)
            for i, embedding in enumerate(embeddings)
        ]


if __name__ == "__main__":
    pipeline = Pipeline(settings.PDF_INPUT_PATH)
    pipeline.run(clear_cache=False)
