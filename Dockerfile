# Stage 1: Build the application with Poetry
FROM python:3.11-slim as builder

# Install poetry
RUN pip install poetry

# Set the working directory
WORKDIR /app

# Copy the project files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-dev

# Copy the rest of the application
COPY . .

# Stage 2: Create the final image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /.venv

# Activate the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy the application code
COPY . .

# Install Playwright browsers
RUN playwright install

# Expose the port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
