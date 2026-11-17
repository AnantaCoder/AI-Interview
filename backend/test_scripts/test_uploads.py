import requests
import tempfile
import os

BASE_URL = "http://127.0.0.1:8000/api/v1"

def create_sample_resume(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def test_resume_category():
    print("Testing /resume/predict-category endpoint...")
    sample_resume_text = "Experienced software engineer with expertise in Python, FastAPI, React, and Machine Learning. Building scalable backend systems."
    response = requests.post(f"{BASE_URL}/resume/predict-category", json={"text": sample_resume_text})
    if response.status_code == 200:
        print("Success! Category predicted:", response.json())
    else:
        print(f"Failed. Status code: {response.status_code}, Response: {response.text}")

def test_ats_evaluate():
    print("Testing /ats/evaluate endpoint...")
    
    resume_path = "temp_resume.txt"
    jd_path = "temp_jd.txt"
    
    resume_text = "I am a skilled Python developer. I know FastAPI and React. I have 5 years of experience."
    jd_text = "We are looking for a Python developer with experience in FastAPI and React."
    
    create_sample_resume(resume_path, resume_text)
    create_sample_resume(jd_path, jd_text)
    
    with open(resume_path, 'rb') as f_resume, open(jd_path, 'rb') as f_jd:
        files = {
            'resume_file': ('temp_resume.txt', f_resume, 'text/plain'),
            'job_desc_file': ('temp_jd.txt', f_jd, 'text/plain')
        }
        response = requests.post(f"{BASE_URL}/ats/evaluate", files=files)
        
    if response.status_code == 200:
        print("Success! ATS Score:", response.json())
    else:
        print(f"Failed. Status code: {response.status_code}, Response: {response.text}")

    # cleanup
    os.remove(resume_path)
    os.remove(jd_path)

if __name__ == "__main__":
    test_resume_category()
    print("-" * 40)
    test_ats_evaluate()
