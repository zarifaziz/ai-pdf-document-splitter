# AI-Powered PDF Document Splitter

This project implements an intelligent PDF document splitter that automatically separates a multi-document PDF into individual files. It uses text analysis, embeddings, and hierarchical clustering to identify document boundaries and group similar content.

## Features

- Extracts text from multi-document PDFs
- Generates embeddings for document content
- Uses hierarchical clustering to group similar documents
- Custom agglomerative clustering implementation that considers both embedding and page distances to ensure clusters of sequential page numbers (see [`clustering.py`](src/splitter/ml_models/clustering.py))
- Applies post-processing to ensure sequential page ranges within clusters
- Outputs individual PDF files for each identified document
- Streamlit UI for easy interaction

## Installation

1. Clone this repository:
```
git clone https://github.com/zarifaziz/ai-pdf-document-splitter.git
cd ai-pdf-document-splitter
```

2. Install dependencies using Poetry:
```
poetry install
```

3. Copy the example environment file and set the env variables necessary:

```sh
cp env.example .env
```

## Running the Application

To run the application, use the following command:

```
python -m src.splitter.main --input-file path/to/your/input.pdf --clear-cache
```


## Repository Structure

- `src/`: Contains the main source code for the PDF splitter.
  - `splitter/`: Core logic for splitting and clustering PDFs.
    - `ml_models/`: Machine learning models for clustering.
    - `pdf_processor.py`: Splits the PDF by page.
    - `text_extractor.py`: Extracts text from PDF pages using OCR.
  - `app/`: Streamlit app for the user interface.
- `notebooks/`: Jupyter notebooks for training and visualization.

## High-Level Solution

### 1. Document Analysis

The input to the system is a long PDF, structured such that each document occupies a consecutive sequence of pages. We use `pypdf` to split the PDF by page, enabling parallel processing and a scalable architecture. This is implemented in [`pdf_processor.py`](src/splitter/processors/pdf_processor.py).

### 2. Document Understanding

- `text_extractor.py` uses `pytesseract` to convert PDF pages to images and extract text from them. This is done efficiently using a multiprocessing pool.
- Embeddings are generated from the extracted text using OpenAI's embedding model. This off-the-shelf model provides good general performance. Future improvements could involve building a custom embedding model or fine-tuning existing ones, possibly using vision transformers for better performance.

### 3. PDF Splitting / Document Clustering

The task is framed as an unsupervised clustering problem, using agglomerative clustering due to the unknown number of clusters. Parameters were optimized using grid search, with the training and visualization process documented in the [`notebooks/`](notebooks/) folder.

#### Iteration Results

| Iteration | Alpha | Distance Threshold | Number of clusters | Adjusted Rand Index (ARI) | Normalised Mutual Information (NMI) |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.9 | 1.5 | 6 | 0.451 | 0.686 |
| 2 | 0.85 | 2.0 | 6 | 0.500 | 0.700 |
| 3 | 0.9 | 2.1 | 4 | 0.630 | 0.689 |

**Preferred Iteration:** Iteration 2 was chosen for its balance between the number of clusters and performance metrics.

### 4. Generating Group Topics

To generate topics/filenames for each split document, we use OpenAI's GPT-4o-mini LLM, which is trained with "Next Token Prediction". This model is effective for topic generation based on context. Generating a topic is a simple task so we went with a smaller, cheaper model.

## Future Work

Future improvements could include:
- Exploring multimodal embedding models to capture more information from the PDF pages 
- Explore more sophisticated document boundary detection and compare with clustering
- Explore dendograph in the UI or some way for the user to tune the granularity of the document splitting interactively
- Parallel processing for large PDFs
- Authentication / Authorization in the app so that multiple users can use it
- Adding a cacheing layer for a user so that the same input PDF doesn't have to be reprocessed
- Storing embeddings in a vector database, managing a separate collection/index per user
