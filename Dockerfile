FROM mcr.microsoft.com/playwright/python:v1.40.0-focal

# ✅ Upgrade pip first (fixes version conflicts)
RUN pip install --no-cache-dir --upgrade pip

# ✅ Create non-root user (pwuser uses UID 1000)
RUN useradd -m -u 1001 user

WORKDIR /home/user/app

# ✅ Copy requirements for layer caching
COPY --chown=user:1001 requirements.txt .

# ✅ Install deps + pydantic-ai from GitHub (NOT on PyPI)
RUN pip install --no-cache-dir -r requirements.txt \
    git+https://github.com/BerriAI/pydantic-ai.git

# ✅ Copy app code
COPY --chown=user:1001 . .

# ✅ Switch to non-root user for security
USER user

# ✅ Playwright + FastAPI production env
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Expose FastAPI port
EXPOSE 7860

# ✅ Production uvicorn with workers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "2"]
