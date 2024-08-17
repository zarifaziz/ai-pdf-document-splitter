import io
import os
import time
import uuid
import zipfile

import redis
import streamlit as st
from rq import Queue

# Connect to Redis
redis_conn = redis.Redis(host="localhost", port=6379)
queue = Queue(connection=redis_conn)


def main():
    """Main function to set up the Streamlit app and handle file uploads and job status."""
    set_page_config()
    display_instructions()

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
            enqueue_pipeline(temp_file_path)

    # Check job status
    if "job_id" in st.session_state or "job_id" in st.query_params:
        job_id = st.session_state.get("job_id") or st.query_params.get("job_id")
        job = queue.fetch_job(job_id)
        if job:
            job = display_job_status(job)
            if job.is_finished:
                st.session_state["job_result"] = job.result
                display_success_message()
                display_download_links(st.session_state["job_result"])
                del st.session_state["job_id"]
                st.query_params.clear()
        else:
            st.error("Job not found")

    # Display download links if job result is in session state
    elif "job_result" in st.session_state:
        display_download_links(st.session_state["job_result"])


def set_page_config():
    """Set the page configuration for the Streamlit app."""
    st.set_page_config(page_title="AI Automated PDF Splitter", layout="wide")


def display_instructions():
    """Display the instructions for using the app."""
    st.title("AI Automated PDF Splitter")
    st.write(
        """
    ### Instructions
    1. Upload a PDF file.
    2. Click on "Run Pipeline" to process the PDF.
    3. Download the split documents using the provided links.
    """
    )


def save_uploaded_file(uploaded_file):
    """Save the uploaded PDF file to a temporary directory."""
    temp_dir = "data/input_pdf"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    temp_file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return temp_file_path


def enqueue_pipeline(temp_file_path):
    """Enqueue the pipeline job to process the uploaded PDF file."""
    job = queue.enqueue("src.web.worker.run_pipeline", temp_file_path)
    st.session_state["job_id"] = job.id
    st.session_state["prev_status"] = None  # Initialize previous status
    st.success(f"Task started with job ID: {job.id}")
    st.query_params.job_id = job.id


def display_job_status(job):
    """Display the status of the job and wait until it is finished."""
    while not job.is_finished:
        current_status = job.get_status()
        if current_status != st.session_state.get("prev_status"):
            st.session_state["prev_status"] = current_status
            st.info(f"Job Status: {current_status}")
        time.sleep(5)  # Wait for 5 seconds before checking again
        job = queue.fetch_job(job.id)  # Re-fetch the job to get the latest status
    return job


def display_success_message():
    """Display a success message when the pipeline is executed successfully."""
    st.markdown(
        """
        <div style="background-color: #d4edda; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
            <h3 style="color: #155724; margin: 0;">Pipeline executed successfully!</h3>
            <p style="color: #155724; margin: 0;">The PDF has been split into individual documents.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )


def create_zip(output_files):
    """Create a ZIP file containing all the output files."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for output_file in output_files:
            zip_file.write(output_file, os.path.basename(output_file))
    zip_buffer.seek(0)
    return zip_buffer


def display_download_links(output_files):
    """Display download links for each output file and a 'Download All' button."""
    unique_id = str(uuid.uuid4())  # Generate a unique identifier
    st.markdown("<h4>Download Split Documents</h4>", unsafe_allow_html=True)
    for idx, output_file in enumerate(output_files):
        st.markdown(f"**Document: {os.path.basename(output_file)}**")
        with open(output_file, "rb") as f:
            st.download_button(
                label="Download",
                data=f,
                file_name=os.path.basename(output_file),
                mime="application/pdf",
                key=f"download_{unique_id}_{idx}",  # Unique key for each download button
                help="Click to download this document",
                use_container_width=False,
            )

    # Add spacing before the "Download All" button
    st.markdown("<br>", unsafe_allow_html=True)

    # Create and provide a download button for the ZIP file
    zip_buffer = create_zip(output_files)
    st.download_button(
        label="Download All",
        data=zip_buffer,
        file_name="all_documents.zip",
        mime="application/zip",
        key=f"download_all_{unique_id}",  # Unique key for the download all button
        help="Click to download all documents as a ZIP file",
        use_container_width=False,
    )


if __name__ == "__main__":
    main()
