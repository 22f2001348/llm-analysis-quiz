import os
import json
import base64
import time
import requests
import io
import pandas as pd
import re
from PyPDF2 import PdfReader
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import google.generativeai as genai
from openai import OpenAI
from urllib.parse import urljoin

load_dotenv()

app = FastAPI()

# --- Configuration ---
SECRET_KEY = os.getenv("QUIZ_SECRET", "default_secret")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "GEMINI")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAX_TIME_PER_TASK = 170
MAX_RETRIES = 3

if LLM_PROVIDER == "GEMINI" and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- Pydantic Models ---
class QuizTask(BaseModel):
    email: str
    secret: str
    url: str

# --- LLM Call ---
def get_llm_response(prompt: str):
    if LLM_PROVIDER == "GEMINI":
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        response = model.generate_content(prompt)
        return response.text
    elif LLM_PROVIDER == "OPENAI":
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Using a more capable model
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    else:
        return "No LLM configured."

# --- File Handling and Data Processing ---
def download_file(url: str) -> bytes:
    response = requests.get(url)
    response.raise_for_status()
    return response.content

def process_pdf(file_content: bytes) -> str:
    pdf_file = io.BytesIO(file_content)
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def process_csv(file_content: bytes) -> str:
    csv_file = io.BytesIO(file_content)
    df = pd.read_csv(csv_file)
    return df.to_string()

def get_file_content_from_page(page, base_url):
    links = page.query_selector_all("a")
    file_content_str = ""
    for link in links:
        href = link.get_attribute("href")
        if not href:
            continue

        file_url = urljoin(base_url, href)
        if file_url.endswith((".pdf", ".csv")):
            print(f"Found file: {file_url}")
            try:
                file_content = download_file(file_url)
                if file_url.endswith(".pdf"):
                    file_content_str += f"Content of {file_url}:\n{process_pdf(file_content)}\n\n"
                elif file_url.endswith(".csv"):
                    file_content_str += f"Content of {file_url}:\n{process_csv(file_content)}\n\n"
            except Exception as e:
                print(f"Failed to download or process {file_url}: {e}")
    return file_content_str

# --- Solver Logic ---
def solve_quiz_and_get_submit_url(page, base_url):
    page_text = page.inner_text("body")
    file_data = get_file_content_from_page(page, base_url)

    prompt = f"""
    You are an expert data analyst. Your task is to solve the quiz based on the provided information.

    Page Text:
    ---
    {page_text}
    ---

    File Content:
    ---
    {file_data if file_data else "No files found."}
    ---

    Carefully analyze the page text and any file content to determine the answer. The page text will contain the submission URL.

    Your response must be a single JSON object with two keys: "submit_url" and "answer".
    - "submit_url": The URL where the answer should be submitted.
    - "answer": The solution to the quiz. If you cannot determine the answer, set this to null.

    Example response:
    ```json
    {{
      "submit_url": "https://example.com/submit",
      "answer": 12345
    }}
    ```
    """

    llm_response_text = get_llm_response(prompt)

    try:
        # Improved JSON extraction from markdown code blocks
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", llm_response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Fallback to the original regex if no markdown block is found
            json_search = re.search(r'\{.*\}', llm_response_text, re.DOTALL)
            if json_search:
                json_str = json_search.group(0)
            else:
                raise ValueError("No JSON object found in LLM response.")

        response_json = json.loads(json_str)
        return response_json.get("submit_url"), response_json.get("answer")

    except (ValueError, json.JSONDecodeError) as e:
        print(f"Could not parse JSON from LLM response: {llm_response_text}, error: {e}")
        return None, "Failed to parse LLM response."

# --- Background Task for Quiz Solving ---
def solve_quiz_in_background(email: str, secret: str, initial_url: str):
    start_time = time.time()
    current_url = initial_url

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        while current_url and (time.time() - start_time) < MAX_TIME_PER_TASK:
            retries = 0
            solved = False
            while retries < MAX_RETRIES and not solved and (time.time() - start_time) < MAX_TIME_PER_TASK:
                try:
                    print(f"Attempt {retries + 1} for quiz at: {current_url}")
                    page.goto(current_url, timeout=60000)
                    submit_url, answer = solve_quiz_and_get_submit_url(page, current_url)

                    if not submit_url:
                        print("Could not determine submission URL. Stopping.")
                        break

                    response_data = submit_answer(submit_url, email, secret, current_url, answer)
                    print(f"Submission response: {response_data}")

                    if response_data.get("correct"):
                        print("Answer was correct. Moving to the next quiz if available.")
                        current_url = response_data.get("url")
                        solved = True
                    else:
                        print(f"Answer was incorrect. Reason: {response_data.get('reason')}")
                        retries += 1
                        time.sleep(5) # Wait before retrying

                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
                    retries += 1
                    time.sleep(5)

            if not solved:
                print("Could not solve the quiz after multiple retries. Stopping.")
                break

            if not current_url:
                print("No new quiz URL provided. Ending quiz.")
                break

        browser.close()

    if (time.time() - start_time) >= MAX_TIME_PER_TASK:
        print("Task timed out after reaching the maximum allowed time.")
    print("Background quiz solving process finished.")


def submit_answer(submit_url: str, email: str, secret: str, original_url: str, answer: any):
    payload = {"email": email, "secret": secret, "url": original_url, "answer": answer}
    try:
        response = requests.post(submit_url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error submitting answer: {e}")
        return {"correct": False, "reason": str(e)}

# --- API Endpoint ---
@app.post("/quiz")
def handle_quiz_task(task: QuizTask, background_tasks: BackgroundTasks):
    if task.secret != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid secret")

    background_tasks.add_task(solve_quiz_in_background, task.email, task.secret, task.url)

    return {"status": "ok", "message": "Quiz solving process started in the background."}
