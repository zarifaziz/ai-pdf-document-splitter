import os
from multiprocessing import Pool

from .pdf_splitter import PdfSplitter
from .settings import settings
from .text_extractor import TextExtractor


class Pipeline:
    def __init__(self, input_file):
        self.input_file = input_file
        self.splitter = PdfSplitter(input_file)
        self.text_extractor = TextExtractor()

    def process_page(self, pdf_path):
        text = self.text_extractor(pdf_path)
        txt_filename = os.path.splitext(os.path.basename(pdf_path))[0] + ".txt"
        txt_path = os.path.join(settings.TXT_OUTPUT_DIR, txt_filename)
        with open(txt_path, "w") as txt_file:
            txt_file.write(text)

    def run(self):
        os.makedirs(settings.PDF_OUTPUT_DIR, exist_ok=True)
        os.makedirs(settings.TXT_OUTPUT_DIR, exist_ok=True)
        
        self.splitter.run()
        pdf_files = [
            os.path.join(settings.PDF_OUTPUT_DIR, f)
            for f in os.listdir(settings.PDF_OUTPUT_DIR)
            if f.endswith(".pdf")
        ]
        with Pool() as pool:
            pool.map(self.process_page, pdf_files)


# Example usage
if __name__ == "__main__":
    pipeline = Pipeline("data/input_pdf/take_home_challenge.pdf")
    pipeline.run()
