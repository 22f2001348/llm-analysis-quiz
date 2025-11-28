# LLM Analysis Quiz Agent (Replicated Architecture)

This project is a highly robust, tool-based autonomous agent designed to solve a series of web-based data analysis quizzes. This version has been meticulously re-architected to mirror a successful project structure, ensuring stability, reliability, and performance.

## Architecture

The project is now organized into a clean, modular structure:

-   **`main.py`**: The FastAPI server that exposes a `/quiz` endpoint. It is responsible for handling incoming requests and launching the agent in a secure, sandboxed background process with a 3-minute timeout.
-   **`agent.py`**: The brain of the application. It uses LangGraph to create a stateful agent that can reason, make decisions, and use tools to solve the quiz tasks. The agent is guided by a highly detailed and strict system prompt.
-   **`tools/`**: A dedicated directory for the agent's capabilities.
    -   **`agent_tools.py`**: Contains the core tools: `get_rendered_html` for web browsing, `download_file` for handling all file types, and a powerful `python_interpreter` for data analysis.
-   **`pyproject.toml`**: A modern, reliable way to manage all project dependencies.

## Key Features

-   **Autonomous Quiz Solving**: Navigates a series of quizzes, starting from a single URL.
-   **Tool-Based Reasoning**: Uses a set of powerful tools to interact with the world, making it highly adaptable.
-   **Robust Error Handling**: Captures and returns errors, allowing the agent to self-correct.
-   **Secure and Configurable**: All secrets and API keys are managed through a `.env` file.
-   **Resilient by Design**: Runs in a separate process with a timeout to prevent hangs.
-   **Cloud-Ready**: The `render.yaml` file is configured for easy deployment on the Render platform.

## How to Run

1.  **Clone the repository.**
2.  **Create a `.env` file** in the root directory with the following:
    ```
    QUIZ_SECRET="your_secret"
    GEMINI_API_KEY="your_gemini_key"
    EMAIL="your_email"
    ```
3.  **Install dependencies and run the server:**
    ```bash
    pip install poetry
    poetry install
    playwright install
    poetry run uvicorn main:app --reload
    ```
