import io
import os
import time
import uuid
import zipfile

import redis
import streamlit as st
from rq import Queue

# Connect to Redis
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_conn = redis.from_url(redis_url)
queue = Queue(connection=redis_conn)


def main():
    """Main function to set up the Streamlit app and handle file uploads and job status."""
    set_page_config()
    display_sidebar()

    st.title("AI Automated PDF Splitter")

    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

    if uploaded_file is not None:
        # Read the file and store it in Redis
        file_content = uploaded_file.read()
        file_key = f"pdf:{uploaded_file.name}"
        redis_conn.set(file_key, file_content)
        st.write(f"Uploaded file: {uploaded_file.name}")

        if st.button("Run Pipeline"):
            split_level = st.session_state.get("split_level", 2.0)
            enqueue_pipeline(file_key, split_level)

            # Check job status
            job_id = st.session_state.get("job_id")
            if job_id:
                job = queue.fetch_job(job_id)
                if job:
                    job = display_job_status(job)
                    if job.is_finished:
                        st.session_state["job_result"] = job.result
                        display_success_message()
                        st.session_state["displayed_links"] = True  # Set flag to indicate links have been displayed
                        st.session_state["output_files"] = job.result  # Store output files in session state
                        display_download_links(st.session_state["output_files"])
                        del st.session_state["job_id"]
                        st.query_params.clear()
                else:
                    st.error("Job not found")

    # Display download links if job result is in session state and links have not been displayed yet
    if "job_result" in st.session_state and not st.session_state.get("displayed_links", False):
        display_download_links(st.session_state["job_result"])
        st.session_state["displayed_links"] = True  # Set flag to indicate links have been displayed

    # Display download links if output files are in session state
    if "output_files" in st.session_state:
        display_download_links(st.session_state["output_files"])


def set_page_config():
    """Set the page configuration for the Streamlit app."""
    st.set_page_config(page_title="AI Automated PDF Splitter", layout="wide")


def display_sidebar():
    """Display the sidebar with instructions and settings."""
    st.sidebar.title("Settings and Instructions")
    st.sidebar.write(
        """
    ### Instructions
    1. Upload a PDF file.
    2. Click on "Run Pipeline" to process the PDF.
    3. Wait for pipeline to complete. This could take a few minutes for large PDFs.
    4. Download the documents using the provided links.
    """
    )
    st.sidebar.write("### Set Clustering Parameters")
    st.sidebar.write(
        """
    The split level setting controls how finely the PDF will be split into individual documents. 
    - **Lower values** (e.g., 0.1) will result in more, smaller documents.
    - **Higher values** (e.g., 5.0) will result in fewer, larger documents.
    
    Adjust the slider to find the right balance for your needs. The recommended value is 2.0, which provides a good balance for most documents.
    """
    )
    st.sidebar.slider(
        "Split Level (Recommended: 2.0)",
        min_value=0.1,
        max_value=5.0,
        value=2.0,
        step=0.1,
        key="split_level",
    )


def enqueue_pipeline(file_key, split_level):
    """Enqueue the pipeline job to process the uploaded PDF file."""
    job = queue.enqueue("src.web.worker.run_pipeline", file_key, split_level)
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
            file_content = redis_conn.get(f"{output_file}")
            zip_file.writestr(os.path.basename(output_file), file_content)
    zip_buffer.seek(0)
    return zip_buffer


def display_download_links(output_files):
    """Display download links for each output file and a 'Download All' button."""
    unique_id = str(uuid.uuid4())  # Generate a unique identifier
    st.markdown("<h4>Download Split Documents</h4>", unsafe_allow_html=True)
    for idx, output_file in enumerate(output_files):
        st.markdown(f"**Document: {os.path.basename(output_file)}**")
        file_content = redis_conn.get(f"{output_file}")
        st.download_button(
            label="Download",
            data=file_content,
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