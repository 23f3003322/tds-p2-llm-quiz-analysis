FROM python:3.11-slim

WORKDIR /app

# Copy only requirements first so Docker can cache layer efficiently
COPY requirements.txt ./

# Install system packages (optional but useful for most deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies + pydantic-ai
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir pydantic-ai

# Copy the rest of the code
COPY . .

# Default command (customize as needed)
CMD ["python", "main.py"]
