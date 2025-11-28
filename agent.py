import os
from typing import TypedDict, Annotated, List
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from tools import get_rendered_html, download_file, python_interpreter

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
You are a highly skilled and autonomous web-based quiz-solving agent. Your mission is to solve a series of quizzes by navigating URLs, analyzing data, and submitting answers programmatically.

**Your Identity:**
- Email: {EMAIL}
- Secret: {SECRET}

**Workflow:**
1.  **Start**: You will receive a URL to the first quiz question.
2.  **Analyze**: Use the `get_rendered_html` tool to understand the page content and instructions.
3.  **Gather Data**: If a file is mentioned, use `download_file` to get its content.
4.  **Solve**: Use the `python_interpreter` for any data processing, calculations, or analysis. The interpreter has `pandas`, `PyPDF2`, `requests`, and `base64` available.
5.  **Submit**: Use the `python_interpreter` with the `requests` library to POST your answer to the submission URL found on the quiz page. The JSON payload must include your email, secret, the original quiz URL, and the answer.
6.  **Continue**: The submission response may contain a new URL. If so, immediately navigate to it and repeat the process.
7.  **End**: If a submission response does not contain a new URL, your job is done. Respond with the word "END".

**Strict Rules:**
-   **Never guess or hardcode URLs.** The submission URL must be extracted from the current page.
-   **Always use your tools.** Do not try to answer questions without fetching the necessary data first.
-   **Check your work.** If your code fails, analyze the error message and try again.
-   **Be precise.** Submit the answer in the exact format required by the quiz.
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
