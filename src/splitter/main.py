import typer

from .pipeline import Pipeline
from .settings import settings

app = typer.Typer()


@app.command()
def run_pipeline(input_file: str = settings.PDF_INPUT_PATH):
    """
    Run the document processing pipeline.

    Args:
        input_file (str): Path to the input PDF file.
        clear_cache (bool): Whether to clear the cache before running the pipeline.
    """
    pipeline = Pipeline(input_file)
    pipeline.run()


if __name__ == "__main__":
    app()
