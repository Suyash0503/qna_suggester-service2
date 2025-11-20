FROM python:3.11-slim

WORKDIR /app

# requirement file
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# microservice folder
COPY . .

# Exposed internal port
EXPOSE 8003

# path for uvicorn entrypoint
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
