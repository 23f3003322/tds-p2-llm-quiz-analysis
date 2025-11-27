FROM python:3.11-slim

RUN useradd -m -u 1000 user

WORKDIR /home/user/app


# Install dependencies
COPY --chown=user ./requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY --chown=user . .

USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH

# Expose port
EXPOSE 7860

# Run with production settings
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
