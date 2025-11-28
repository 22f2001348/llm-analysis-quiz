import multiprocessing
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv

# Import the compiled agent application
from agent import agent_app

# Load environment variables from a .env file
load_dotenv()

# Initialize the FastAPI application
app = FastAPI(title="LLM Quiz Agent", version="1.0.0")

# --- Configuration ---
# Load the secret key from environment variables for endpoint security
SECRET_KEY = os.getenv("QUIZ_SECRET")
# Set a hard timeout for each quiz task to ensure resilience
TASK_TIMEOUT = 180  # 3 minutes

# --- Pydantic Models ---
class QuizTask(BaseModel):
    """Defines the structure of the incoming quiz task request."""
    email: str
    secret: str
    url: str

def run_agent_process(initial_url: str):
    """
    The target function that runs the agent in a separate process.
    This sandboxing is crucial for managing the agent's lifecycle and timeout.
    """
    try:
        # Provide the initial message to kick off the agent's workflow
        initial_message = ("user", f"Start the quiz at this URL: {initial_url}")

        # Invoke the LangGraph agent with the initial message
        agent_app.invoke(
            {"messages": [initial_message]},
            # Set a high recursion limit to allow for complex, multi-step tasks
            config={"recursion_limit": 150},
        )
        print("Agent process finished successfully.")
    except Exception as e:
        # Log any errors that occur within the agent process for debugging
        print(f"Agent process encountered a critical error: {e}")

# --- Background Task Definition ---
def solve_quiz_in_background(initial_url: str):
    """
    Launches the agent in a separate, timed process to handle the quiz task.
    This ensures the main server remains responsive.
    """
    print(f"Starting agent for URL: {initial_url}")
    # Create a new process to run the agent, ensuring isolation
    process = multiprocessing.Process(target=run_agent_process, args=(initial_url,))
    process.start()

    # Wait for the process to complete, with a hard timeout
    process.join(timeout=TASK_TIMEOUT)

    # If the process is still running after the timeout, terminate it
    if process.is_alive():
        process.terminate()
        process.join()
        print(f"Task timed out after {TASK_TIMEOUT} seconds and was terminated.")
    else:
        print("Task finished within the time limit.")

# --- API Endpoint ---
@app.post("/quiz")
def handle_quiz_task(task: QuizTask, background_tasks: BackgroundTasks):
    """
    The main API endpoint that receives quiz tasks, validates them,
    and dispatches them to the agent in the background.
    """
    # Security check: Validate the incoming secret key
    if task.secret != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid secret key provided.")

    # Add the agent task to FastAPI's background tasks to run after the response is sent
    background_tasks.add_task(solve_quiz_in_background, task.url)

    # Return an immediate success response to the client
    return {"status": "ok", "message": "Quiz solving process has been started in the background."}
