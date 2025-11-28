# LLM Analysis Quiz Agent (Tool-Based)

This project is a highly robust, tool-based autonomous agent designed to solve a series of web-based data analysis quizzes. Built with FastAPI, LangGraph, and Google's Gemini LLM, this agent can browse websites, download files, and execute Python code to perform complex data analysis tasks.

## Architecture

This project has been re-architected from a monolithic design to a modular, agent-based system that mirrors the successful approach of modern AI applications.

-   **`main.py`**: The FastAPI server that exposes a `/quiz` endpoint to receive tasks. It launches the agent as a background process with a 3-minute timeout to ensure resilience.
-   **`agent.py`**: The core of the application. It uses LangGraph to create a stateful agent that can reason and decide which tool to use. The agent is guided by a detailed system prompt that ensures it follows a strict, logical workflow.
-   **`tools.py`**: A collection of tools the agent can use:
    -   `get_rendered_html`: Browses a URL and returns the full, JavaScript-rendered HTML.
    -   `download_file`: Downloads any file (text or binary) and returns its content as a base64-encoded string.
    -   `python_interpreter`: A sandboxed Python interpreter with `pandas`, `PyPDF2`, `requests`, and `base64` for data analysis and submission.

## Key Features

-   **Autonomous Quiz Solving**: The agent can navigate a series of quizzes, starting from an initial URL.
-   **Tool-Based Reasoning**: The agent uses a set of tools to interact with the world, making it highly flexible and adaptable.
-   **Robust Error Handling**: The `python_interpreter` tool captures and returns errors, allowing the agent to self-correct.
-   **Secure and Configurable**: All secrets and API keys are managed through environment variables.
-   **Resilient by Design**: The agent runs in a separate process with a timeout, preventing it from getting stuck.
-   **Cloud-Ready**: The `render.yaml` file provides a complete configuration for deploying on the Render platform.

## How to Run

1.  **Clone the repository.**
2.  **Create a `.env` file** with the following:
    ```
    QUIZ_SECRET="your_secret"
    GEMINI_API_KEY="your_gemini_key"
    EMAIL="your_email"
    ```
3.  **Install dependencies and run the server:**
    ```bash
    pip install -r requirements.txt
    playwright install
    uvicorn main:app --reload
    ```
