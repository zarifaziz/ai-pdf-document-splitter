import os
import shutil
from typing import Dict, List

from .domain_models import Document, PageInfo
from .ml_models.clustering import perform_agglomerative_clustering, perform_boundary_detection_clustering
from .ml_models.embedding import (generate_embeddings, load_embeddings,
                                  save_embeddings)
from .processors.document_processor import (assign_topics_to_documents,
                                            create_documents)
from .processors.pdf_processor import PDFMerger
from .processors.text_extractor import TextExtractor
from .settings import settings

from loguru import logger

class Pipeline:
    def __init__(self, input_file: str) -> None:
        """Initialize the Pipeline with the input file and text extractor."""
        self.input_file = input_file
        self.text_extractor = TextExtractor()

    def run(self, clear_cache: bool = True) -> List[str]:
        """Execute the entire pipeline process."""
        if clear_cache:
            logger.info("Clearing cache.")
            self.clear_cache()

        logger.info("Extracting texts from PDFs.")
        self.text_extractor.extract_texts_from_pdfs(self.input_file)
        
        logger.info("Reading extracted texts.")
        texts = self.text_extractor.read_extracted_texts()
        logger.info(f"Number of texts extracted: {len(texts)}") 
        
        logger.info("Generating embeddings.")
        embeddings = generate_embeddings(self.input_file, texts)
        save_embeddings(self.input_file, embeddings)
        embeddings = load_embeddings(self.input_file)
        
        page_infos = self.create_page_infos(embeddings)
        
        logger.info("Performing clustering.")
        clusters = perform_agglomerative_clustering(embeddings)
        
        documents = create_documents(page_infos, clusters)

        logger.info(f"Number of documents created: {len(documents)}")
        logger.info("Assigning topics to documents.")
        documents = assign_topics_to_documents(documents, texts)

        self.output_pdf_split_results(documents)
        
        output_files = self.create_pdf_documents(documents)

        logger.info("Pipeline execution completed.")
        return output_files

    def clear_cache(self) -> None:
        """Clear the temporary and output directories and delete .pkl files from data/."""
        directories_to_clear = [
            settings.TEMP_PDF_PAGES_DIR,
            settings.TEMP_IMAGE_DIR,
            settings.TXT_OUTPUT_DIR,
            settings.OUTPUT_DOCS_DIR,
        ]
        for directory in directories_to_clear:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        logger.error(f"Failed to delete {file_path}. Reason: {e}")
            else:
                logger.warning(f"Directory {directory} does not exist.")

        data_directory = "data"
        if os.path.exists(data_directory):
            for filename in os.listdir(data_directory):
                if filename.endswith(".pkl"):
                    file_path = os.path.join(data_directory, filename)
                    try:
                        os.unlink(file_path)
                    except Exception as e:
                        logger.error(f"Failed to delete {file_path}. Reason: {e}")
        else:
            logger.warning(f"Directory {data_directory} does not exist.")

    def output_pdf_split_results(self, documents_dict: Dict[int, Document]) -> None:
        """Print the clustering results for each document."""
        for document in documents_dict.values():
            logger.info(
                f"Document ID: {document.id}, Topic: {document.topic_name}, Page Range: {document.page_range}"
            )

    def create_pdf_documents(self, documents: Dict[int, Document]) -> List[str]:
        """Create PDF documents from the clustered pages and return their paths."""
        pdf_merger = PDFMerger(self.input_file)
        output_files = []
        for id, document in documents.items():
            output_file = os.path.join(
                settings.OUTPUT_DOCS_DIR, f"document_{id}_{document.topic_name}.pdf"
            )
            page_numbers = [page.page_number for page in document.pages]
            pdf_merger.merge_pages(page_numbers, output_file)
            output_files.append(output_file)
        output_files.sort()
        return output_files

    def create_page_infos(self, embeddings: List) -> List[PageInfo]:
        """Create PageInfo objects from the embeddings."""
        return [
            PageInfo(input_pdf_path=self.input_file, page_number=i, embedding=embedding)
            for i, embedding in enumerate(embeddings)
        ]
