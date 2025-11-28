# Autonomous LLM-Powered Data Analysis Quiz Agent

## Overview

This project implements a sophisticated, autonomous agent designed to solve complex, multi-step data analysis quizzes. Leveraging a tool-based architecture powered by LangGraph and Google's Gemini Pro, the agent can navigate web pages, download and analyze various file types (including PDFs and CSVs), and submit its findings programmatically.

This repository is a meticulously engineered solution, mirroring a proven, successful project structure to ensure maximum reliability and performance.

---

## Architectural Design

The application is built on a modular, professional-grade architecture that separates concerns for clarity, maintainability, and robustness.

-   **`main.py`**: The core of the web service, this file implements a FastAPI server that exposes a single `/quiz` endpoint. It is responsible for validating incoming requests and launching the agent in a secure, sandboxed background process. A 3-minute timeout ensures that the agent is resilient to hangs or unexpected delays.

-   **`agent.py`**: The "brain" of the operation. This module defines the agent's logic using LangGraph, creating a stateful, reasoning engine. The agent is guided by a highly detailed and strict system prompt that dictates its workflow and decision-making process.

-   **`tools/`**: This directory encapsulates the agent's capabilities, providing a clean separation between the agent's logic and its ability to interact with the environment.
    -   **`agent_tools.py`**: Contains the core toolset:
        -   `get_rendered_html`: A powerful tool that uses a headless browser to fetch the full, JavaScript-rendered HTML of a web page.
        -   `download_file`: A robust tool capable of downloading any file type (text or binary) and returning its content as a base64-encoded string for analysis.
        -   `python_interpreter`: A sandboxed Python environment with `pandas`, `PyPDF2`, `requests`, and `base64` pre-loaded, allowing the agent to perform complex data analysis and submit its answers.

-   **`pyproject.toml`**: Utilizes modern Python packaging standards to manage all project dependencies, ensuring reproducible builds.

-   **`Dockerfile`**: A professional, multi-stage Dockerfile that creates a lean, optimized production image, making the project highly portable and easy to deploy in any containerized environment.

---

## Key Features

-   **Autonomous, End-to-End Operation**: The agent can navigate a series of quizzes, starting from a single URL, without human intervention.
-   **Advanced Tool-Based Reasoning**: The agent's ability to use a set of powerful tools makes it highly adaptable to a wide range of data analysis challenges.
-   **Self-Correcting Error Handling**: The `python_interpreter` is designed to capture and return errors, allowing the agent to debug its own code and try again.
-   **Secure and Configurable**: All sensitive information, such as API keys and secrets, is managed through a `.env` file, following security best practices.
-   **Resilient by Design**: The agent runs in a separate process with a hard timeout, preventing it from getting stuck and ensuring the server remains responsive.
-   **Cloud-Ready**: The `render.yaml` file is pre-configured for seamless deployment on the Render platform.

---

## Getting Started

### Prerequisites

-   Python 3.11+
-   Poetry for dependency management
-   A Google Gemini API Key

### Installation and Local Execution

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Create a `.env` file** in the root directory and populate it with your credentials:
    ```
    QUIZ_SECRET="your_secret_here"
    GEMINI_API_KEY="your_gemini_api_key"
    EMAIL="your_email@example.com"
    ```

3.  **Install dependencies using Poetry and set up Playwright:**
    ```bash
    pip install poetry
    poetry install
    playwright install
    ```

4.  **Launch the server:**
    ```bash
    poetry run uvicorn main:app --reload
    ```
The server will be available at `http://127.0.0.1:8000`.
