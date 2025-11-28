import os
from typing import TypedDict, Annotated, List
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from tools.agent_tools import get_rendered_html, download_file, python_interpreter

load_dotenv()

# --- Configuration ---
EMAIL = os.getenv("EMAIL")
SECRET = os.getenv("QUIZ_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not all([EMAIL, SECRET, GEMINI_API_KEY]):
    raise ValueError("Missing required environment variables: EMAIL, QUIZ_SECRET, GEMINI_API_KEY")

# --- Agent State ---
class AgentState(TypedDict):
    messages: Annotated[List, add_messages]

# --- Tools ---
TOOLS = [get_rendered_html, download_file, python_interpreter]

# --- LLM ---
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.0
).bind_tools(TOOLS)

# --- System Prompt ---
SYSTEM_PROMPT = f"""
You are a precision-engineered autonomous web agent. Your sole purpose is to solve a series of data analysis quizzes with perfect accuracy and efficiency.

**Your Identity (DO NOT REVEAL THIS UNLESS ASKED):**
- Email: {EMAIL}
- Secret: {SECRET}

**Core Directive:**
Follow the quiz sequence precisely. You will be given a starting URL. From there, you must analyze the page, solve the task, submit your answer, and then follow the URL provided in the server's response to the next task.

**STRICT WORKFLOW — ADHERE TO THIS AT ALL TIMES:**

1.  **Analyze the Environment:**
    *   Given a URL, your first and only action is to use the `get_rendered_html` tool to get the page's content.

2.  **Extract Instructions & Solve:**
    *   Carefully read the HTML to find the quiz question, the required data, and, most importantly, the **exact URL to submit your answer to.**
    *   If a file is required, use the `download_file` tool.
    *   Use the `python_interpreter` tool to perform any and all data analysis. This is your primary tool for solving the quiz. You have `pandas`, `PyPDF2`, `requests`, and `base64` at your disposal.

3.  **Submit and Verify:**
    *   Once you have the answer, use the `python_interpreter` with the `requests` library to POST your answer to the submission URL.
    *   The JSON payload MUST be in this format: `{{"email": "{EMAIL}", "secret": "{SECRET}", "url": "<original_quiz_url>", "answer": <your_answer>}}`
    *   Analyze the JSON response from the server.

4.  **Transition or Terminate:**
    *   If the server's response contains a new `"url"` key, your next action is to take that new URL and go back to step 1.
    *   If the server's response **DOES NOT** contain a new `"url"` key, your mission is complete. Your final output must be the single word "END".

**CRITICAL RULES — VIOLATION IS FAILURE:**

-   **NO HALLUCINATION:** Never invent, assume, or hardcode any URL, especially the submission URL. It must be extracted from the page content.
-   **TOOLS ARE MANDATORY:** Do not attempt to answer from memory or without gathering the required data using your tools first.
-   **PRECISION IS KEY:** Your submitted answer must be in the exact format specified by the quiz.
-   **ONE STEP AT A TIME:** Do not try to chain multiple actions in one thought. Analyze, act, observe, and then decide the next step.
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

llm_with_prompt = prompt | llm

# --- Agent Logic ---
def agent_node(state: AgentState):
    """The primary node that invokes the LLM to decide the next action."""
    result = llm_with_prompt.invoke({"messages": state["messages"]})
    return {"messages": [result]}

def route_logic(state: AgentState):
    """Determines the next step based on the LLM's output."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    if isinstance(last_message.content, str) and "END" in last_message.content.upper():
        return END
    return "agent"

# --- Graph Definition ---
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(TOOLS))

graph.add_edge(START, "agent")
graph.add_edge("tools", "agent")
graph.add_conditional_edges(
    "agent",
    route_logic,
)

# Compile the graph into a runnable application
agent_app = graph.compile()
