# Runs the FastAPI course automation application in Docker.

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install --no-cache-dir -r /app/backend/requirements.txt \
    && pip install --no-cache-dir fastapi uvicorn \
    && playwright install --with-deps chromium

COPY backend /app/backend
COPY frontend /app/frontend
COPY run.py /app/run.py

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]