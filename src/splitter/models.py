from pydantic import BaseModel
import numpy as np
from typing import List, Tuple

class PageInfo(BaseModel):
    input_pdf_path: str
    page_number: int
    embedding: np.ndarray

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            np.ndarray: lambda v: v.tolist()
        }

class Document(BaseModel):
    id: str
    topic: str  # topic of the set of pages
    pages: List[PageInfo]
    page_range: Tuple[int, int]
