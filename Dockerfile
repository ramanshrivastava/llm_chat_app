FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY pyproject.toml .
COPY README.md .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "main.py"] 