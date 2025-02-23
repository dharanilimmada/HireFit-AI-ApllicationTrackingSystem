from dotenv import load_dotenv
import streamlit as st
import google.generativeai as genai
import os
import docx2txt
import PyPDF2 as pdf

# Load environment variables from a .env file
load_dotenv()

# Configure the generative AI model with the Google API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Set up the model configuration for text generation
generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 4096,
}

# Define safety settings for content generation
safety_settings = [
    {"category": f"HARM_CATEGORY_{category}", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
    for category in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]
]

def generate_response_from_gemini(input_text):
    # Create a GenerativeModel instance with 'gemini-pro' as the model type
    llm = genai.GenerativeModel(
        model_name="gemini-pro",
        generation_config=generation_config,
        safety_settings=safety_settings,
    )
    # Generate content based on the input text
    output = llm.generate_content(input_text)
    # Return the generated text
    return output.text

def extract_text_from_pdf_file(uploaded_file):
    # Use PdfReader to read the text content from a PDF file
    pdf_reader = pdf.PdfReader(uploaded_file)
    text_content = ""
    for page in pdf_reader.pages:
        text_content += str(page.extract_text())
    return text_content

def extract_text_from_docx_file(uploaded_file):
    # Use docx2txt to extract text from a DOCX file
    return docx2txt.process(uploaded_file)

# Prompt Templates
input_prompt_evaluation = """
You are an experienced Technical Human Resource Manager. Review the resume provided against the job description.
Highlight strengths and weaknesses of the candidate's profile in relation to the job requirements.
resume:{text}
description:{job_description}
"""

input_prompt_percentage = """
You are a skilled ATS scanner. Evaluate the resume against the job description. Provide a percentage match,
list missing keywords, and offer final thoughts.
resume:{text}
description:{job_description}
I want the response to follow this structure:
"Match Percentage: xx%"
"Missing Keywords: "
"Final Thoughts: "
"""

# Streamlit App Setup
st.title("HireFit AI - The Intelligent Resume ATS")
st.markdown('<style>h1{color: orange; text-align: center; white-space: nowrap;}</style>', unsafe_allow_html=True)
job_description = st.text_area("Paste the Job Description", height=300)
uploaded_file = st.file_uploader("Upload Your Resume", type=["pdf", "docx"], help="Please upload a PDF or DOCX file")

# Buttons for each functionality
submit_evaluation = st.button("Tell Me About the Resume")
submit_percentage = st.button("Percentage Match")

# Process and generate responses based on button clicks
if submit_evaluation or submit_percentage:
    if uploaded_file is not None:
        if uploaded_file.type == "application/pdf":
            resume_text = extract_text_from_pdf_file(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            resume_text = extract_text_from_docx_file(uploaded_file)

        if submit_evaluation:
            response_text = generate_response_from_gemini(input_prompt_evaluation.format(text=resume_text, job_description=job_description))
            st.subheader("Evaluation Response:")
            st.write(response_text)
        
        elif submit_percentage:
            response_text = generate_response_from_gemini(input_prompt_percentage.format(text=resume_text, job_description=job_description))
            st.subheader("Match Percentage Response:")
            st.write(response_text)

            # Attempt to extract match percentage from the response text
            try:
                # Look for patterns in the response to find the match percentage
                lines = response_text.splitlines()
                match_percentage = None
                missing_keywords = ""
                final_thoughts = ""

                for line in lines:
                    if "Match Percentage:" in line:
                        match_percentage = line.split("Match Percentage:")[1].strip().replace('%', '')
                    elif "Missing Keywords:" in line:
                        missing_keywords = line.split("Missing Keywords:")[1].strip()
                    elif "Final Thoughts:" in line:
                        final_thoughts = line.split("Final Thoughts:")[1].strip()

                if match_percentage is not None:
                    match_percentage = float(match_percentage)

                    # Display match percentage and additional information
                    st.write(f"**Match Percentage:** {match_percentage}%")
                    st.write(f"**Missing Keywords:** {missing_keywords}")
                    st.write(f"**Final Thoughts:** {final_thoughts}")

                    # Display message based on match percentage
                    if match_percentage >= 80:
                        st.text("Move forward with hiring")
                    else:
                        st.text("Not a Match")
                else:
                    st.error("Match percentage not found in the response.")

            except Exception as e:
                st.error(f"An error occurred while processing the response: {e}")

    else:
        st.warning("Please upload a resume and enter the job description.")
