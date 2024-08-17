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
        try:
            for page_number in page_numbers:
                writer.add_page(self.reader.pages[page_number])
        except IndexError as e:
            raise IndexError(
                f"Page number {page_number} is out of range for the input file."
            ) from e

        with open(output_file, "wb") as outfile:
            writer.write(outfile)


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
