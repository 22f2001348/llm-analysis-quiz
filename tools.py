import requests
from playwright.sync_api import sync_playwright
import io
import sys
from contextlib import redirect_stdout
import base64
import pandas as pd
from PyPDF2 import PdfReader

def get_rendered_html(url: str) -> str:
    """
    Fetches the rendered HTML of a URL using a headless browser.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        html = page.content()
        browser.close()
    return html

def download_file(url: str) -> str:
    """
    Downloads a file from a URL and returns its content as a base64-encoded string.
    This is suitable for both text and binary files.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        encoded_content = base64.b64encode(response.content).decode('utf-8')
        return encoded_content
    except requests.exceptions.RequestException as e:
        return f"Error downloading file: {e}"

def python_interpreter(code: str) -> str:
    """
    Executes Python code in a controlled environment and returns the output.
    """
    # SECURITY NOTE: This function uses exec(), which is a security risk.
    # It is used here in a sandboxed environment for a specific academic project.
    # Do not use this in a production environment.

    # Create a string buffer to capture stdout
    buffer = io.StringIO()

    # Redirect stdout to the buffer
    with redirect_stdout(buffer):
        try:
            # Create a restricted global environment with necessary libraries
            restricted_globals = {
                "__builtins__": __builtins__,
                "requests": requests,
                "io": io,
                "pd": pd,
                "PdfReader": PdfReader,
                "base64": base64,
            }
            exec(code, restricted_globals)
        except Exception as e:
            # If there's an error, print it to the buffer
            print(e)

    # Get the content of the buffer
    output = buffer.getvalue()

    return output
