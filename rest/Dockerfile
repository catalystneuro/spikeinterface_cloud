FROM python:3.10-slim

# Install PostgreSQL development files
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . ./
ENV SI_CLOUD_ENV production

# Get Python stdout logs
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]