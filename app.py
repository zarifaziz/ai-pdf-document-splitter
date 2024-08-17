import streamlit as st
import redis
from rq import Queue
import os
import time

# Connect to Redis
redis_conn = redis.Redis(host='localhost', port=6379)
queue = Queue(connection=redis_conn)

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
            st.info("Enqueuing the pipeline task.")
            job = queue.enqueue('worker.run_pipeline', temp_file_path)
            st.session_state['job_id'] = job.id
            st.success(f"Task started with job ID: {job.id}")
            st.experimental_set_query_params(job_id=job.id)

    # Check job status
    if 'job_id' in st.session_state or 'job_id' in st.experimental_get_query_params():
        job_id = st.session_state.get('job_id') or st.experimental_get_query_params().get('job_id')
        job = queue.fetch_job(job_id)
        if job:
            st.write(f"Job Status: {job.get_status()}")
            if job.is_finished:
                st.write("Pipeline executed successfully! The PDF has been split into individual documents.")
                output_files = job.result
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
                del st.session_state['job_id']
                st.experimental_set_query_params()
            else:
                time.sleep(5)  # Wait for 5 seconds before rerunning
                st.experimental_set_query_params(job_id=job_id)
        else:
            st.error("Job not found")

if __name__ == "__main__":
    main()