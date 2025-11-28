import os
import json
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chat_models import init_chat_model
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated, List
import multiprocessing
import time

# Import tools
from tools import get_rendered_html, download_file, python_interpreter

load_dotenv()

app = FastAPI()

# --- Configuration ---
SECRET_KEY = os.getenv("QUIZ_SECRET", "default_secret")
EMAIL = os.getenv("EMAIL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TASK_TIMEOUT = 180  # 3 minutes

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

# --- Pydantic Models ---
class QuizTask(BaseModel):
    email: str
    secret: str
    url: str

# --- Agent State ---
class AgentState(TypedDict):
    messages: Annotated[List, add_messages]

# --- Tools ---
TOOLS = [get_rendered_html, download_file, python_interpreter]

# --- LLM ---
llm = init_chat_model(
    model_provider="google_genai",
    model="gemini-1.5-flash",
    google_api_key=GEMINI_API_KEY,
).bind_tools(TOOLS)

# --- System Prompt ---
SYSTEM_PROMPT = f"""
You are an autonomous quiz-solving agent. Your goal is to solve a series of quizzes by navigating through URLs.

Here's your workflow:
1.  **Start with a URL**: You will be given an initial URL.
2.  **Analyze the page**: Use the `get_rendered_html` tool to get the content of the page.
3.  **Find the instructions**: Read the HTML to understand the quiz question, find the submission URL, and determine what data you need.
4.  **Gather data**: If the quiz requires a file, use the `download_file` tool.
5.  **Process and analyze**: Use the `python_interpreter` to analyze the data and find the answer. You can use any library available in a standard Python environment (e.g., pandas, numpy).
6.  **Submit the answer**: Construct a JSON payload with your email, secret, the quiz URL, and your answer. Then, use the `python_interpreter` with the `requests.post` to submit your answer.
7.  **Get the next URL**: The response from the submission will contain the next quiz URL. If there is no new URL, your task is complete.

Your available tools are:
- `get_rendered_html(url: str)`: Fetches the HTML of a page.
- `download_file(url: str)`: Downloads a file.
- `python_interpreter(code: str)`: Executes Python code.

Important notes:
-   Your email is `{EMAIL}` and your secret is `{SECRET_KEY}`.
-   Always use the full URL provided in the quiz. Do not shorten or modify it.
-   When you are done, respond with "END".
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

llm_with_prompt = prompt | llm

# --- Agent Node ---
def agent_node(state: AgentState):
    result = llm_with_prompt.invoke({"messages": state["messages"]})
    return {"messages": [result]}

# --- Graph ---
def route(state):
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    if isinstance(last.content, str) and "END" in last.content:
        return END
    return "agent"

graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(TOOLS))
graph.add_edge(START, "agent")
graph.add_edge("tools", "agent")
graph.add_conditional_edges(
    "agent",
    route,
)

app_graph = graph.compile()

def run_quiz_agent(initial_url: str):
    """The target function for the multiprocessing Process."""
    try:
        app_graph.invoke(
            {"messages": [("user", f"Start with this URL: {initial_url}")]},
            config={"recursion_limit": 50},
        )
        print("Quiz solving process completed successfully.")
    except Exception as e:
        print(f"An error occurred during the quiz solving process: {e}")

# --- Background Task for Quiz Solving ---
def solve_quiz_in_background(initial_url: str):
    process = multiprocessing.Process(target=run_quiz_agent, args=(initial_url,))
    process.start()
    process.join(timeout=TASK_TIMEOUT)

    if process.is_alive():
        process.terminate()
        process.join()
        print(f"Task timed out after {TASK_TIMEOUT} seconds and was terminated.")
    else:
        print("Task finished within the time limit.")

# --- API Endpoint ---
@app.post("/quiz")
def handle_quiz_task(task: QuizTask, background_tasks: BackgroundTasks):
    if task.secret != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid secret")

    background_tasks.add_task(solve_quiz_in_background, task.url)
    return {"status": "ok", "message": "Quiz solving process started in the background."}
