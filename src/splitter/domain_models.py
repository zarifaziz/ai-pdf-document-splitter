from typing import List, Tuple

import numpy as np
from pydantic import BaseModel, Field


class PageInfo(BaseModel):
    page_number: int = Field(..., description="The page number within the PDF")
    input_pdf_path: str = Field(..., description="The path to the input PDF file")
    embedding: np.ndarray = Field(
        ..., description="The embedding vector representing the page content"
    )

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {np.ndarray: lambda v: v.tolist()}


class Document(BaseModel):
    id: str = Field(..., description="Unique identifier for the document")
    topic_name: str = Field(..., description="Topic of the set of pages")
    pages: List[PageInfo] = Field(
        ...,
        description="List of PageInfo objects representing the pages in the document",
    )
    page_range: Tuple[int, int] = Field(
        ..., description="Tuple indicating the range of pages in the document"
    )
