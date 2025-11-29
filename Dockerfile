FROM python:3.11-slim
FROM mcr.microsoft.com/playwright/python:v1.40.0-focal

RUN useradd -m -u 1001 user

WORKDIR /home/user/app


# Install dependencies
COPY --chown=user ./requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt 

COPY --chown=user . .

USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH  PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
# Expose port
EXPOSE 7860

# Run with production settings
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
