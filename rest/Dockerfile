# Dockerfile for the backend
FROM python:3.9-slim

WORKDIR /app

COPY rest/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY rest ./

EXPOSE 5000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]