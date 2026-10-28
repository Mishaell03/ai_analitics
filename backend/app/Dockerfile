FROM python:3.13-slim

WORKDIR /srv
COPY app/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY app app
COPY infra/llm/context.md infra/llm/context.md

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 65534:65534
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
