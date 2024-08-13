# AI-Powered PDF Document Splitter

This project implements an intelligent PDF document splitter that automatically separates a multi-document PDF into individual files. It uses text analysis, embeddings, and hierarchical clustering to identify document boundaries and group similar content.

## Features

- Extracts text from multi-document PDFs
- Generates embeddings for document content
- Uses hierarchical clustering to group similar documents
- Applies post-processing to ensure sequential page ranges within clusters
- Outputs individual PDF files for each identified document

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


## Running the Application

To run the application, use the following command:

```
python -m src.splitter.main --input-file path/to/your/input.pdf --clear-cache
```

## Limitations and Future Work

- Currently optimized for PDFs where each document occupies a continuous range of pages.
- Future improvements could include:
- More sophisticated document boundary detection
- Support for non-sequential document arrangements
- GUI for easier user interaction
- Parallel processing for large PDFs
