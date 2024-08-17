import os
from typing import List
import redis
from pypdf import PdfReader, PdfWriter

from ..settings import settings

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_conn = redis.from_url(redis_url)

class PDFMerger:
    def __init__(self, input_file: str):
        """Initialize the PDFMerger with the input file."""
        self.input_file = input_file
        self.reader = PdfReader(input_file)
        os.makedirs(settings.TEMP_PDF_PAGES_DIR, exist_ok=True)
        os.makedirs(settings.OUTPUT_DOCS_DIR, exist_ok=True)

    def merge_pages(self, page_numbers: List[int], output_file: str):
        """Merge specified pages into a single output file."""
        writer = PdfWriter()
        try:
            for page_number in page_numbers:
                writer.add_page(self.reader.pages[page_number])
        except IndexError as e:
            raise IndexError(
                f"Page number {page_number} is out of range for the input file."
            ) from e

        # Write to Redis
        output_key = f"merged:{output_file}"
        with open(output_file, "wb") as outfile:
            writer.write(outfile)
        
        # Read the file content after closing the writer
        with open(output_file, "rb") as outfile:
            redis_conn.set(output_key, outfile.read())


class PDFSplitter:
    def __init__(self, input_file):
        self.input_file = input_file
        self.file_name = os.path.splitext(os.path.basename(input_file))[0]
        os.makedirs(settings.TEMP_PDF_PAGES_DIR, exist_ok=True)

    def run(self):
        with open(self.input_file, "rb") as infile:
            reader = PdfReader(infile)
            for i in range(len(reader.pages)):
                writer = PdfWriter()
                writer.add_page(reader.get_page(i))

                output_filename = (
                    f"{settings.TEMP_PDF_PAGES_DIR}/{self.file_name}_page_{i + 1}.pdf"
                )
                with open(output_filename, "wb") as outfile:
                    writer.write(outfile)
