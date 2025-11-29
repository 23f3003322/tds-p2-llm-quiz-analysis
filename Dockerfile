FROM mcr.microsoft.com/playwright/python:v1.40.0-focal

# ✅ Create user with UID 1001 (pwuser uses 1000)
RUN useradd -m -u 1001 user

WORKDIR /home/user/app

# ✅ Copy requirements first for better caching
COPY --chown=user:1001 requirements.txt .

# ✅ Install dependencies including pydantic-ai
RUN pip install --no-cache-dir -r requirements.txt pydantic-ai

# Copy application code
COPY --chown=user:1001 . .

# Switch to non-root user
USER user

# ✅ Playwright + FastAPI environment
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Expose port
EXPOSE 7860

# Run with production settings
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "2"]
