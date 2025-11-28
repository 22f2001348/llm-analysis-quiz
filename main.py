import multiprocessing
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv

from agent import agent_app

load_dotenv()

app = FastAPI()

# --- Configuration ---
SECRET_KEY = os.getenv("QUIZ_SECRET")
TASK_TIMEOUT = 180  # 3 minutes

# --- Pydantic Models ---
class QuizTask(BaseModel):
    email: str
    secret: str
    url: str

def run_agent_process(initial_url: str):
    """Target function for the multiprocessing Process to run the agent."""
    try:
        # The initial message to kick off the agent
        initial_message = ("user", f"Start the quiz at this URL: {initial_url}")

        # Invoke the agent graph
        agent_app.invoke(
            {"messages": [initial_message]},
            config={"recursion_limit": 50},  # Safety limit for recursion
        )
        print("Agent process finished successfully.")
    except Exception as e:
        print(f"Agent process encountered an error: {e}")

# --- Background Task Definition ---
def solve_quiz_in_background(initial_url: str):
    """
    Launches the agent in a separate process with a timeout.
    """
    process = multiprocessing.Process(target=run_agent_process, args=(initial_url,))
    process.start()
    process.join(timeout=TASK_TIMEOUT)

    if process.is_alive():
        process.terminate()
        process.join()
        print(f"Task timed out after {TASK_TIMEOUT} seconds and was terminated.")

# --- API Endpoint ---
@app.post("/quiz")
def handle_quiz_task(task: QuizTask, background_tasks: BackgroundTasks):
    """
    Handles incoming quiz tasks, verifies the secret, and starts the
    agent in a background process.
    """
    if task.secret != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid secret key.")

    # Add the agent task to be run in the background
    background_tasks.add_task(solve_quiz_in_background, task.url)

    return {"status": "ok", "message": "Quiz solving process has been started in the background."}
