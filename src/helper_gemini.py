import os
import fitz  # PyMuPDF
from dotenv import load_dotenv, find_dotenv
from google import genai
from google.genai import types
from google.genai import errors
import re

from src.prompt import RESUME_ANALYSIS_PROMPT
load_dotenv(find_dotenv())




# ----------------------------
# Vertex AI config
# ----------------------------

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not GOOGLE_CLOUD_PROJECT:
    raise ValueError(
        "GOOGLE_CLOUD_PROJECT is missing. Add it to your .env file."
    )

client = genai.Client(
    vertexai=True,
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
    http_options=types.HttpOptions(api_version="v1"),
)


# ----------------------------
# PDF extraction
# ----------------------------

def extract_text_from_pdf(uploaded_file):
    """
    Extract text from uploaded PDF resume.
    """
    uploaded_file.seek(0)

    doc = fitz.open(
        stream=uploaded_file.read(),
        filetype="pdf",
    )

    text = ""

    for page in doc:
        text += page.get_text()

    doc.close()

    return text.strip()


# ----------------------------
# Gemini call
# ----------------------------

def ask_gemini(prompt, max_tokens=3000):
    """
    Send prompt to Gemini and return response text.
    Handles errors safely so Streamlit does not crash.
    """
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=max_tokens,
            ),
        )

        return response.text.strip() if response.text else "No response generated."

    except errors.ClientError as e:
        error_text = str(e)

        if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
            return (
                "⚠️ Gemini quota or rate limit reached.\n\n"
                "Your current Gemini/Vertex AI quota has been exceeded. "
                "Please wait, reduce repeated requests, check billing/quota, "
                "or try again later."
            )

        return f"Gemini API error: {e}"

    except Exception as e:
        return f"Unexpected Gemini error: {e}"


# ----------------------------
# Resume analysis
# ----------------------------

def analyze_resume_with_gemini(resume_text, max_tokens=2500):
    """
    Compact resume analysis for Streamlit display.
    Also includes job search keywords, so we do not need another Gemini call.
    """
    prompt = RESUME_ANALYSIS_PROMPT.format(resume_text=resume_text)

    return ask_gemini(prompt, max_tokens=max_tokens)


# ----------------------------
# Extract keywords without another Gemini call
# ----------------------------

def extract_job_keywords(resume_analysis):
    """
    Extract job search keywords from the Gemini resume analysis.
    This avoids making a second Gemini API call.
    """
    pattern = r"## 🔎 Job Search Keywords\s*(.*)"
    match = re.search(pattern, resume_analysis, re.DOTALL)

    if not match:
        return ""

    keywords_text = match.group(1).strip()

    # Remove markdown bullets if Gemini accidentally adds them
    keywords_text = keywords_text.replace("-", "")
    keywords_text = keywords_text.replace("*", "")
    keywords_text = keywords_text.replace("\n", " ")

    # Keep only content before another section if Gemini adds extra headings
    keywords_text = keywords_text.split("##")[0].strip()

    return keywords_text