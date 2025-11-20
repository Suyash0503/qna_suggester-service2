FROM python:3.11-slim

WORKDIR /app

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy microservice contents
COPY . .

# Expose port for FastAPI
EXPOSE 80
USER root 
# Run QnA microservice
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
