
import streamlit as st
from pypdf import PdfReader
from docx import Document
from io import BytesIO

st.set_page_config(
    page_title="HireSense AI",
    page_icon="📄",
    layout="wide"
)

st.title("HireSense AI")
st.subheader("AI-Based Resume Screening and Job Matching System")

st.write(
    "Upload your resume to extract its content "
    "and prepare it for AI-based analysis."
)

uploaded_file = st.file_uploader(
    "Upload your Resume",
    type=["pdf", "docx"]
)

if uploaded_file is not None:

    file_name = uploaded_file.name
    file_bytes = uploaded_file.getvalue()

    extracted_text = ""

    try:
        if file_name.lower().endswith(".pdf"):
            pdf = PdfReader(BytesIO(file_bytes))

            for page in pdf.pages:
                extracted_text += page.extract_text() or ""

        elif file_name.lower().endswith(".docx"):
            document = Document(BytesIO(file_bytes))

            for paragraph in document.paragraphs:
                extracted_text += paragraph.text + "\n"

        st.success("Resume uploaded successfully!")

        st.subheader("Extracted Resume Text")
        st.text_area(
            "Resume Content",
            extracted_text,
            height=300
        )

        if not extracted_text.strip():
            st.warning(
                "No readable text was found. "
                "The PDF may be scanned or image-based."
            )

    except Exception as error:
        st.error("Unable to process this resume.")
        st.exception(error)
