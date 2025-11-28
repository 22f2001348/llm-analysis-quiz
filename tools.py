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
    Fetches the rendered HTML of a URL using a headless browser.
    This is useful for pages that are heavily rendered with JavaScript.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            # Wait for network to be idle, which is a good signal that JS has finished
            page.wait_for_load_state("networkidle")
            html = page.content()
            browser.close()
        return html
    except Exception as e:
        return f"Error rendering HTML for {url}: {e}"


def download_file(url: str) -> str:
    """
    Downloads a file from a URL and returns its content as a base64-encoded string.
    This is suitable for both text and binary files like PDFs or images.
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        encoded_content = base64.b64encode(response.content).decode('utf-8')
        return encoded_content
    except requests.exceptions.RequestException as e:
        return f"Error downloading file from {url}: {e}"


def python_interpreter(code: str) -> str:
    """
    Executes Python code in a controlled environment and returns the output,
    including any errors. This tool has access to libraries like pandas,
    PyPDF2, requests, and base64 for data analysis and manipulation.
    """
    # SECURITY NOTE: This function uses exec(), which is a security risk.
    # It is used here in a sandboxed environment for a specific academic project.
    # Do not use this in a production environment without extreme caution.
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        try:
            # Provide a restricted global environment with necessary libraries
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
            # If there's an error, print it to the buffer to be returned
            print(e, file=sys.stdout)

    return buffer.getvalue()
