import base64
import io
import sys
from contextlib import redirect_stdout

import pandas as pd
import requests
from PyPDF2 import PdfReader
from playwright.sync_api import sync_playwright


def get_rendered_html(url: str) -> str:
    """
    Fetches the fully rendered HTML of a URL using a headless browser.
    This is essential for modern web pages that rely heavily on JavaScript.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # Set a generous timeout for page navigation
            page.goto(url, timeout=60000)
            # Wait for the network to be idle, a reliable indicator that JS rendering is complete
            page.wait_for_load_state("networkidle")
            html = page.content()
            browser.close()
        return html
    except Exception as e:
        # Return a clear error message if any part of the process fails
        return f"Error rendering HTML for {url}: {e}"


def download_file(url: str) -> str:
    """
    Downloads any file from a URL and returns its content as a base64-encoded string.
    This approach is robust for both text-based and binary files (e.g., PDFs, images).
    """
    try:
        response = requests.get(url, timeout=30)
        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()
        # Encode the raw binary content into a UTF-8 string for safe JSON transport
        encoded_content = base64.b64encode(response.content).decode('utf-8')
        return encoded_content
    except requests.exceptions.RequestException as e:
        return f"Error downloading file from {url}: {e}"


def python_interpreter(code: str) -> str:
    """
    Executes a string of Python code in a controlled, sandboxed environment.
    This tool is the agent's primary means of performing data analysis, manipulation,
    and making HTTP requests. It captures and returns all stdout and errors.
    """
    # --- SECURITY WARNING ---
    # This function uses exec(), which is a significant security risk if used in an
    # uncontrolled environment. It is implemented here for a specific, sandboxed
    # academic project. Do not use this in a production environment without
    # implementing stringent security measures.

    # Use a string buffer to capture all output from the executed code
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        try:
            # Provide a restricted global environment to the exec call.
            # This environment contains only safe, necessary libraries.
            restricted_globals = {
                "__builtins__": __builtins__,
                "requests": requests,
                "pd": pd,
                "PdfReader": PdfReader,
                "base64": base64,
                "io": io,
            }
            exec(code, restricted_globals)
        except Exception as e:
            # If any exception occurs during code execution, print it to the
            # buffer so the agent can receive the error message and self-correct.
            print(e, file=sys.stdout)

    # Return the complete captured output as a string
    return buffer.getvalue()
