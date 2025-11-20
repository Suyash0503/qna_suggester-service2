from pydantic import BaseModel
from typing import List

class TopicQuestionsModel(BaseModel):
    topic: str
    static_questions: List[str] = []
    ai_questions: List[str] = []
    merged: List[str] = []

class CachedQnAModel(BaseModel):
    topics: List[TopicQuestionsModel] = []
    suggestions: List[str] = []
