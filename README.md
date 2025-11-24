# LLM Analysis Quiz Agent

This project is an automated agent designed to solve a series of data analysis and visualization quizzes. The agent is built with FastAPI and uses Playwright for headless browsing and a configurable LLM (Gemini or OpenAI) for reasoning and problem-solving.

## Core Features

- **Automated Quiz Solving**: The agent can navigate to a quiz URL, analyze the content, and solve the given task.
- **Headless Browser Integration**: Uses Playwright to handle JavaScript-rendered pages and interact with web elements.
- **LLM-Agnostic Design**: Easily switch between LLM providers (Gemini and OpenAI) using environment variables.
- **Robust Task Loop**: The agent can handle multi-step quizzes by automatically submitting answers and navigating to the next task URL.
- **Secure Endpoint**: The API endpoint is secured with a secret key to prevent unauthorized access.
- **Cloud-Native**: Designed to be deployed on cloud platforms like Render, with configuration provided in `render.yaml`.

## Tech Stack

- **Backend**: FastAPI
- **Headless Browser**: Playwright
- **LLM Integration**: Google Generative AI (for Gemini), OpenAI API (placeholder)
- **HTTP Client**: requests
- **Deployment**: Render

## Design Choices

- **Stateless Architecture**: The agent is stateless, meaning it doesn't store any information about past quizzes. This simplifies the design and makes it more reliable, which aligns with the linear, one-way nature of the quiz.
- **LLM as the "Brain"**: Instead of writing complex parsing logic for every possible quiz format, the agent offloads the reasoning to a large language model. This makes the agent more flexible and adaptable to different types of questions.
- **Environment Variables for Configuration**: All sensitive information (API keys, secrets) and configuration (LLM provider) is handled through environment variables, which is a security best practice.
- **Render for Deployment**: Render was chosen for its ease of use, free tier, and seamless integration with GitHub, making deployment straightforward. The `render.yaml` file automates the setup process.

## How to Run Locally

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd llm-analysis-quiz
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    playwright install
    ```

3.  **Create a `.env` file** with the following content:
    ```
    QUIZ_SECRET="your_secret_here"
    LLM_PROVIDER="GEMINI" # or OPENAI
    GEMINI_API_KEY="your_gemini_api_key"
    # OPENAI_API_KEY="your_openai_api_key"
    ```

4.  **Run the application:**
    ```bash
    uvicorn fastapi_quiz_agent:app --reload
    ```

## API Endpoint

The agent exposes a single endpoint: `POST /quiz`.

**Request Body:**

```json
{
  "email": "your.email@example.com",
  "secret": "your_secret_here",
  "url": "https://example.com/quiz-url"
}
```

**Responses:**

- `200 OK`: If the secret is valid and the quiz loop starts.
- `403 Forbidden`: If the secret is invalid.
- `500 Internal Server Error`: If an error occurs during the quiz-solving process.
