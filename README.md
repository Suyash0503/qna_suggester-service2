QnA Suggester Service

The QnA Suggester Service is a cloud-ready microservice designed to generate relevant interview questions based on user-provided job details and skills. It combines rule-based filtering with transformer-based language model inference to provide contextual and role-specific interview preparation support.

This service is built using FastAPI and integrates a Hugging Face transformer model for dynamic question generation. It is designed for deployment on AWS and uses DynamoDB for NoSQL data storage.

Project Overview

The service accepts structured JSON input including:

Job title

Resume skills (resume.skills)

Job description keywords (jd.keywords)

Optional suggestion flag

It processes the input and returns:

Categorized interview questions

Role-specific technical questions

General preparation tips (optional)

The system combines predefined QnA mappings with transformer-based inference to generate relevant and contextual responses.

Architecture

Client → REST API (FastAPI) → QnA Processing Layer
↓
Hugging Face Model Inference
↓
DynamoDB (NoSQL Storage)

Core Features

REST API built with FastAPI

Transformer-based question generation using google/flan-t5-small

Hybrid static + AI-driven question generation

NoSQL integration with DynamoDB

Swagger/OpenAPI documentation

Cloud deployment ready (AWS)

Optional Docker containerization

Technology Stack

Python 3

FastAPI

Hugging Face Transformers

google/flan-t5-small

DynamoDB (AWS NoSQL)

Docker

AWS ECS / EC2 deployment ready

API Input Format

Example request body:

{
  "resume": {
    "skills": ["Python", "AWS", "Docker"]
  },
  "jd": {
    "keywords": ["backend", "microservices"]
  },
  "suggestions": true
}
API Output Format

Example response:

{
  "topics": {
    "Python": [
      "Explain decorators in Python.",
      "What are generators and when would you use them?"
    ],
    "AWS": [
      "What is the difference between EC2 and ECS?",
      "Explain DynamoDB partition keys."
    ]
  },
  "general_tips": [
    "Revise system design fundamentals.",
    "Practice explaining trade-offs clearly."
  ]
}
Running Locally

Install dependencies:

pip install -r requirements.txt

Start the FastAPI server:

uvicorn main:app --reload

Access interactive API documentation:

http://127.0.0.1:8000/docs
Docker Usage

Build Docker image:

docker build -t qna-suggester .

Run container:

docker run -p 8000:8000 qna-suggester
AWS Deployment

The service is designed for deployment on:

AWS ECS

AWS EC2

AWS Elastic Beanstalk

AWS App Runner

Deployment workflow:

Containerize the application

Push image to Amazon ECR

Deploy to ECS or other AWS service

Configure environment variables

Connect DynamoDB tables

Environment Variables

Example configuration:

AWS_REGION=us-east-1
DYNAMODB_TABLE=qna_data
MODEL_NAME=google/flan-t5-small
Design Highlights

Hybrid approach combining static curated data with transformer-based inference

Scalable NoSQL architecture using DynamoDB

RESTful interface for integration with web or mobile frontends

Structured JSON schema for extensibility

Cloud-native deployment strategy

Future Enhancements

Resume upload parsing (PDF to structured JSON)

Personalized scoring system

Fine-tuned domain-specific language model

CI/CD integration

Authentication and rate limiting

Analytics and performance tracking

Author

Suyash
Cloud and Distributed Systems
Microservices | AWS | FastAPI | AI Integration
