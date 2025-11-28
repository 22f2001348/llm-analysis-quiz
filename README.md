# LLM Analysis Quiz Agent

## Project Overview

This is an autonomous agent designed to solve a series of web-based data analysis quizzes. The agent is built with FastAPI and uses a tool-based architecture with LangGraph and Google's Gemini Pro to navigate web pages, download files, perform data analysis, and submit answers.

The architecture of this project is based on a proven, reliable structure to ensure stable and consistent performance.

---

## Architecture

The application is organized into a modular structure to keep the code clean and maintainable.

-   **`main.py`**: This file contains the FastAPI server. It provides a `/quiz` endpoint that accepts POST requests and starts the agent in a background process. To prevent hangs, the agent process is terminated after a 3-minute timeout.

-   **`agent.py`**: This is the core logic of the agent. It uses LangGraph to define a state machine that can reason and decide which tool to use. The agent is guided by a strict system prompt that outlines its workflow.

-   **`tools/agent_tools.py`**: This file contains the tools the agent can use to interact with the quiz environment:
    -   `get_rendered_html`: Uses a headless browser (Playwright) to get the full HTML of a page, including content rendered by JavaScript.
    -   `download_file`: Downloads a file from a URL and returns its content as a base64-encoded string, which works for both text and binary files.
    -   `python_interpreter`: A sandboxed Python environment that allows the agent to execute code for data analysis. It has `pandas`, `PyPDF2`, `requests`, and `base64` available.

-   **`pyproject.toml`**: Manages the project's dependencies using Poetry.

-   **`Dockerfile`**: A multi-stage Dockerfile is included for building a production-ready container image.

---

## How to Run Locally

### Prerequisites

-   Python 3.11+
-   Poetry
-   A Google Gemini API Key

### Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Create a `.env` file** in the root of the project and add your credentials:
    ```
    QUIZ_SECRET="your_secret_here"
    GEMINI_API_KEY="your_gemini_api_key"
    EMAIL="your_email@example.com"
    ```

3.  **Install dependencies:**
    ```bash
    pip install poetry
    poetry install
    playwright install
    ```

4.  **Run the server:**
    ```bash
    poetry run uvicorn main:app --reload
    ```
The application will be running at `http://127.0.0.1:8000`.
