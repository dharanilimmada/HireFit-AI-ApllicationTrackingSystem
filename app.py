from dotenv import load_dotenv
import base64
import streamlit as st
import os
import io
from PIL import Image
import pdf2image
import google.generativeai as genai

# Load environment variables and configure Generative AI API
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(input_text, pdf_content, prompt):
    model = genai.get_model('models/gemini-1.5-flash')  # Ensure you're using the correct model name
    
    # Use the correct method for generating text
    response = model.generate(
        input=input_text,
        context=[pdf_content[0]["data"], prompt],  # Ensure this is the right context structure
        generation_config={
            "max_output_tokens": 8192,
            "temperature": 1,
            "top_p": 0.95,
        }
    )
    return response.text if response else "No response generated"

def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        try:
            # Convert PDF to image with explicit Poppler path
            images = pdf2image.convert_from_bytes(
                uploaded_file.read(), 
                poppler_path=r"C:\Program Files\poppler\Library\bin"
            )

            # Take only the first page of the PDF
            first_page = images[0]
            img_byte_arr = io.BytesIO()
            first_page.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()

            pdf_parts = [
                {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(img_byte_arr).decode()  # Encode to base64
                }
            ]
            return pdf_parts
        except FileNotFoundError:
            st.error("Poppler not found. Please make sure Poppler is installed and the path is correctly specified.")
            return None
        except Exception as e:
            st.error(f"Error processing PDF: {e}")
            return None
    else:
        st.error("No file uploaded")
        return None

# Streamlit App Configuration
st.set_page_config(page_title="ATS Resume Expert")
st.header("HireFit AI")
input_text = st.text_area("Job Description: ", key="input")
uploaded_file = st.file_uploader("Upload your resume (PDF)...", type=["pdf"])

# Button triggers
submit1 = st.button("Tell Me About the Resume")
submit3 = st.button("Percentage match")

# Prompt texts
input_prompt1 = """
You are an experienced Technical Human Resource Manager. Your task is to review the provided resume against the job description. 
Please share your professional evaluation on whether the candidate's profile aligns with the role. 
Highlight the strengths and weaknesses of the applicant in relation to the specified job requirements.
"""

input_prompt3 = """
You are a skilled ATS (Applicant Tracking System) scanner with a deep understanding of data science and ATS functionality. 
Your task is to evaluate the resume against the provided job description. Give me the percentage of match if the resume matches
the job description. First, the output should come as a percentage, followed by missing keywords and then final thoughts.
"""

# Processing input and generating response based on button pressed
if submit1 or submit3:
    if uploaded_file is not None and input_text:
        pdf_content = input_pdf_setup(uploaded_file)
        if pdf_content is not None:  # Ensure pdf_content is valid
            if submit1:
                response = get_gemini_response(input_text, pdf_content, input_prompt1)
                st.subheader("Evaluation Response")
                st.write(response)
            elif submit3:
                response = get_gemini_response(input_text, pdf_content, input_prompt3)
                st.subheader("Match Percentage Response")
                st.write(response)
    else:
        st.warning("Please upload the resume and enter the job description.")
