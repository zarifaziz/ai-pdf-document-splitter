from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""

    PDF_INPUT_DIR: str = "data/input_pdf"
    TEMP_PDF_PAGES_DIR: str = "data/temp_pdf_pages"
    TEMP_IMAGE_DIR: str = "data/temp_images"
    TXT_OUTPUT_DIR: str = "data/txt_pages"
    OUTPUT_DOCS_DIR: str = "data/output_docs"

    class Config:
        env_file = ".env"


settings = Settings()
