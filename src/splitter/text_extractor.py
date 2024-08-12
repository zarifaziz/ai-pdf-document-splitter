import os
import re
import uuid
from pathlib import Path
from typing import List

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path

from .settings import settings


class TextExtractor:
    """
    Class for extracting text from PDF documents and images.
    """

    def __init__(self, delete_temp_images: bool = True):
        """Initializes the DocProcessor with a temporary image file directory."""
        self.temp_image_dir = str(settings.TEMP_IMAGE_DIR)
        self.delete_temp_images = delete_temp_images
        if not os.path.exists(self.temp_image_dir):
            os.makedirs(self.temp_image_dir)

    def __call__(self, file_path: str) -> str:
        """
        Extracts text from the specified file path.

        Parameters
        ----------
        file_path : str
            The path to the file or directory from which to extract text.

        Returns
        -------
        str
            The extracted text.
        """
        text = self.extract_text(file_path)
        return text

    def extract_text(self, file_path: str) -> str:
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
        text = ""
        if os.path.isdir(file_path):
            for file in os.listdir(file_path):
                if (
                    file.endswith(".pdf")
                    or file.endswith(".jpg")
                    or file.endswith(".png")
                ):
                    new_text = self.get_text(
                        self.file_to_image(Path(file_path, file).as_posix())
                    )
                    if new_text:
                        text += new_text + "\n"
        elif os.path.isfile(file_path) and (
            file_path.endswith(".pdf")
            or file_path.endswith(".jpg")
            or file_path.endswith(".png")
        ):
            text = self.get_text(self.file_to_image(file_path))
        return text

    def get_text(self, image_list: List[np.ndarray]) -> str:
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
            words = self.clean_text(words)
            text.append(words)
        text = [x for x in text if len(x) > 1]
        text = "\n".join(text)
        return text

    def file_to_image(self, file_path: str) -> List[np.ndarray]:
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

    def clean_text(self, words: str) -> str:
        """
        Cleans and formats extracted text.
        NOT IMPLEMENTED FOR MVP.

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
