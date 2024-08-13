import os
from typing import List

from pypdf import PdfReader, PdfWriter

from ..settings import settings


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
        for page_number in page_numbers:
            writer.add_page(self.reader.pages[page_number])

        with open(output_file, "wb") as outfile:
            writer.write(outfile)
