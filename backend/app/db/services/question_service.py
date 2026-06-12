import os
import json
from dotenv import load_dotenv

load_dotenv(override=True)

try:
    from google import genai
    USING_NEW_SDK = True
except ImportError:
    import google.generativeai as genai
    USING_NEW_SDK = False


async def generate_questions_for_role(job_role, num_questions: int, question_type: str, difficulty: str) -> list[dict]:
    """
    Generates interview questions and model answers based on the job role.
    Uses Gemini AI.
    """
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")

    skills_str = ", ".join(job_role.required_skills) if isinstance(job_role.required_skills, list) else str(job_role.required_skills)
    pref_skills_str = ", ".join(job_role.preferred_skills) if isinstance(job_role.preferred_skills, list) else str(job_role.preferred_skills)

    prompt = f"""You are a senior technical interviewer and hiring manager.
Generate {num_questions} interview questions of difficulty level '{difficulty}' for the following job role:

Job Title: {job_role.title}
Job Description: {job_role.description or 'No description provided'}
Required Skills: {skills_str or 'None'}
Preferred Skills: {pref_skills_str or 'None'}
Experience Requirement: {job_role.min_experience_years} years

Question Type Requested: {question_type}

For each question, generate:
1. The question text.
2. The question type (must be one of: 'technical', 'behavioral', 'situational').
3. The expected ideal model answer (a concise but comprehensive model answer explaining what a good response covers).
4. A list of 4-8 expected answer keywords/phrases that a good answer should contain.

Return the response strictly in JSON format as a list of objects like this:
[
  {{
    "question_text": "question string",
    "question_type": "technical" | "behavioral" | "situational",
    "expected_answer": "ideal answer string",
    "expected_answer_keywords": ["keyword1", "keyword2", ...]
  }}
]
Do not include any markdown formatting (such as ```json or ```). Just return the raw JSON array.
"""

    if USING_NEW_SDK:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        text_response = response.text
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([prompt])
        text_response = response.text if response else None

    if not text_response:
        raise ValueError("No response received from Gemini API")

    # Clean markdown code block wraps if present
    text_response = text_response.replace("```json", "").replace("```", "").strip()

    try:
        questions = json.loads(text_response)
        if not isinstance(questions, list):
            raise ValueError("Gemini response is not a JSON list")
        return questions
    except json.JSONDecodeError as e:
         raise ValueError(f"Failed to parse Gemini response as JSON: {e}. Raw response: {text_response}")
