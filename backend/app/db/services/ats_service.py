import os
import json
import fitz
from docx import Document
from dotenv import load_dotenv

load_dotenv()

# We try to import google-genai, fallback to older module if needed, although user specifically asked for latest.
try:
    from google import genai
    from google.genai import types
except ImportError:
    import google.generativeai as genai
    
def extract_text(file_path):
    file_extension = file_path.split(".")[-1].lower()
    try:
        if file_extension == "pdf": 
            doc = fitz.open(file_path)
            # PyMuPDF extraction
            text = " ".join([page.get_text() for page in doc])
        elif file_extension in ["docx", "doc"]:
            doc = Document(file_path)
            text = " ".join([para.text for para in doc.paragraphs])
        elif file_extension == "txt":
            with open(file_path, "r", encoding="utf-8") as file:
                text = file.read()
        else:
            print("Unsupported format. Use PDF, DOCX, or TXT.")
            return None
        return text
    except Exception as e:
        print(f"Text extraction error: {e}")
        return None

def get_ats_score(resume_text, job_desc_text):
    prompt = f"""You are a skilled Human Resource ATS scanner. Evaluate the resume against the job description. 
Provide the percentage match, followed by missing keywords, final thoughts, and concrete suggestions for improvement.

Score them out of 100.
    
Resume:
{resume_text}

Job Description:
{job_desc_text}

Return the response strictly in JSON format as follows:
{{
    "percentage_match": "85%",
    "missing_keywords": ["keyword1", "keyword2"],
    "suggestions": ["suggestion1", "suggestion2"],
    "final_thoughts": "your detailed thoughts here"
}}
"""
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return {"error": "API key not found"}
            
        try:
            # New google-genai 1.0+ SDK usage
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            text_response = response.text
        except Exception:
             # Fallback to the older syntax just in case package resolution was partial
             genai.configure(api_key=api_key)
             model = genai.GenerativeModel("gemini-2.5-flash")
             response = model.generate_content([prompt])
             text_response = response.text if response else None
             
        if not text_response:
             return {"error": "No Response from API"}
             
        # Clean up JSON formatting from the LLM (remove markdown if it included it)
        text_response = text_response.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(text_response)
        except json.JSONDecodeError:
            return {"error": "Failed to parse API response into JSON", "raw_response": text_response}
    except Exception as e:
        return {"error": f"API error: {str(e)}"}
