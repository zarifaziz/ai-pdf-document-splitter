import streamlit as st
from src.splitter.pipeline import Pipeline
from src.splitter.settings import settings
import os
import time

def main():
    st.set_page_config(page_title="AI Automated PDF Splitter", layout="wide")
    st.title("AI Automated PDF Splitter")

    st.write("""
    ### Instructions
    1. Upload a PDF file.
    2. Click on "Run Pipeline" to process the PDF.
    3. Download the split documents using the provided links.
    """)

    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

    if uploaded_file is not None:

        # Ensure the directory exists
        temp_dir = "data/input_pdf"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Save the uploaded file to a temporary location
        temp_file_path = os.path.join("data/input_pdf", uploaded_file.name)
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.write(f"Uploaded file: {uploaded_file.name}")

        if not os.path.exists(temp_file_path):
            st.error(f"File not found: {temp_file_path}")
            return

        if st.button("Run Pipeline"):
            st.info("Running the pipeline to extract text, generate embeddings, and cluster documents.")
            st.info("This may take a few minutes, please wait...")
            progress_bar = st.progress(0)
            
            pipeline = Pipeline(temp_file_path)
            output_files = pipeline.run()
            
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)

            st.success("Pipeline executed successfully! The PDF has been split into individual documents.")

            # Display and provide download links for the output documents
            for output_file in output_files:
                st.write(f"Document: {os.path.basename(output_file)}")
                with open(output_file, "rb") as f:
                    st.download_button(
                        label="Download",
                        data=f,
                        file_name=os.path.basename(output_file),
                        mime="application/pdf",
                    )

if __name__ == "__main__":
    main()