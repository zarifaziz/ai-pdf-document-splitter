import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path

from ..settings import settings
from .pdf_processor import PDFSplitter
from loguru import logger

class TextExtractor:
    """
    Class for extracting text from PDF documents and images.
    """

    def __init__(self, delete_temp_images: bool = True):
        """Initializes the TextExtractor with a temporary image file directory."""
        self.temp_image_dir = str(settings.TEMP_IMAGE_DIR)
        self.delete_temp_images = delete_temp_images
        os.makedirs(self.temp_image_dir, exist_ok=True)
        os.makedirs(settings.TXT_OUTPUT_DIR, exist_ok=True)

    def extract_texts_from_pdfs(self, input_file: str) -> None:
        """
        Splits the input PDF into individual pages and extracts text from each page.

        Parameters
        ----------
        input_file : str
            The path to the input PDF file.
        """
        splitter = PDFSplitter(input_file)
        splitter.run()
        pdf_files: List[str] = [
            os.path.join(settings.TEMP_PDF_PAGES_DIR, f)
            for f in os.listdir(settings.TEMP_PDF_PAGES_DIR)
            if f.endswith(".pdf")
        ]
        with ThreadPoolExecutor() as executor:
            executor.map(
                TextExtractor.convert_pdf_to_text,
                pdf_files,
            )
            executor.shutdown(wait=True)
        logger.debug("extract_texts_from_pdfs: all threads complete")

    def read_extracted_texts(self) -> List[str]:
        """
        Reads the extracted text files from the output directory.

        Returns
        -------
        List[str]
            A list of strings, each containing the text from a single page.
        """
        text_files = [
            os.path.join(settings.TXT_OUTPUT_DIR, f)
            for f in os.listdir(settings.TXT_OUTPUT_DIR)
            if f.endswith(".txt")
        ]
        texts = []
        for text_file in text_files:
            with open(text_file, "r") as file:
                texts.append(file.read())
        return texts

    def extract_text_from_file(self, file_path: str) -> str:
        """
        Extracts text from files in the specified directory or from a single file.

        Parameters
        ----------
        file_path : str
            The path to the file or directory from which to extract text.

        Returns
        -------
        str
            The extracted text.
        """
        logger.debug(f"Starting text extraction from file: {file_path}")
        text = ""
        if os.path.isdir(file_path):
            logger.debug(f"{file_path} is a directory. Processing files inside.")
            for file in os.listdir(file_path):
                logger.debug(f"Processing file: {file}")
                if (
                    file.endswith(".pdf")
                    or file.endswith(".jpg")
                    or file.endswith(".png")
                ):
                    logger.debug(f"File {file} is a supported format. Extracting text.")
                    new_text = self.extract_text_from_images(
                        self.convert_file_to_images(Path(file_path, file).as_posix())
                    )
                    if new_text:
                        logger.debug(f"Extracted text from {file}.")
                        text += new_text + "\n"
        elif os.path.isfile(file_path):
            logger.debug(f"{file_path} is a file.")
            if (
                file_path.endswith(".pdf")
                or file_path.endswith(".jpg")
                or file_path.endswith(".png")
            ):
                logger.debug(f"File {file_path} is a supported format. Extracting text.")
                text = self.extract_text_from_images(self.convert_file_to_images(file_path))
        logger.debug(f"Completed text extraction from file: {file_path}")
        return text

    def extract_text_from_images(self, image_list: List[np.ndarray]) -> str:
        """
        Extracts text from a list of images.

        Parameters
        ----------
        image_list : List[np.ndarray]
            A list of images from which to extract text.

        Returns
        -------
        str
            The extracted text.
        """
        text = []
        for image in image_list:
            words = pytesseract.image_to_string(image, config="--psm 1 --oem 1")
            words = self.clean_extracted_text(words)
            text.append(words)
        text = [x for x in text if len(x) > 1]
        text = "\n".join(text)
        return text

    def convert_file_to_images(self, file_path: str) -> List[np.ndarray]:
        """
        Converts files to images for text extraction.

        Parameters
        ----------
        file_path : str
            The path to the file to convert to an image.

        Returns
        -------
        List[np.ndarray]
            A list of images in numpy array format.
        """
        image_list = []
        temp_files = []
        if file_path.endswith(".pdf"):
            images = convert_from_path(file_path)
            for page in images:
                temp_image_filedir = os.path.join(
                    self.temp_image_dir, f"{uuid.uuid4()}.jpg"
                )
                page.save(temp_image_filedir, "JPEG")
                image_list.append(self.preprocess_image(temp_image_filedir))
                temp_files.append(temp_image_filedir)
        elif file_path.endswith(".png") or file_path.endswith(".jpg"):
            image_list.append(self.preprocess_image(file_path))
        if self.delete_temp_images:
            for temp_file in temp_files:
                os.remove(temp_file)
        return image_list

    def preprocess_image(self, file_path: str) -> np.ndarray:
        """
        Preprocesses images for text extraction, converting them from BGR to RGB format
        needed for pytesseract.

        Parameters
        ----------
        file_path : str
            The path to the image file to preprocess.

        Returns
        -------
        np.ndarray
            The preprocessed image in numpy array format.
        """
        image = cv2.imread(file_path)
        image = image[..., ::-1]  # Convert BGR to RGB
        return image

    def clean_extracted_text(self, words: str) -> str:
        """
        Cleans and formats extracted text.

        Parameters
        ----------
        words : str
            The raw text extracted from an image or document.

        Returns
        -------
        str
            The cleaned and formatted text.
        """
        return words

    @classmethod
    def convert_pdf_to_text(cls, pdf_path: str) -> None:
        """
        Converts a PDF file to text and saves it to the output directory.

        Parameters
        ----------
        pdf_path : str
            The path to the PDF file to convert.
        """
        logger.debug(f"convert_pdf_to_text: Starting processing for {pdf_path}")
        
        # Initialize TextExtractor
        logger.debug("Initializing TextExtractor instance.")
        text_extractor = cls()
        
        # Extract text from the PDF file
        logger.debug(f"Extracting text from file: {pdf_path}")
        text = text_extractor.extract_text_from_file(pdf_path)
        logger.debug("extraction done")
        
        # Generate the output text file path
        txt_filename = os.path.splitext(os.path.basename(pdf_path))[0] + ".txt"
        txt_path = os.path.join(settings.TXT_OUTPUT_DIR, txt_filename)
        logger.debug(f"Generated text file path: {txt_path}")
        
        # Write the extracted text to the output file
        logger.debug(f"Writing extracted text to {txt_path}")
        with open(txt_path, "w") as txt_file:
            txt_file.write(text)
        
        logger.debug(f"convert_pdf_to_text: Completed processing for {pdf_path}")
