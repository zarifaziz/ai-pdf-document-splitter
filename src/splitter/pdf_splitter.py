import os

from pypdf import PdfReader, PdfWriter

from .settings import settings


class PdfSplitter:
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


if __name__ == "__main__":
    splitter = PdfSplitter("input.pdf")
    splitter.run()
