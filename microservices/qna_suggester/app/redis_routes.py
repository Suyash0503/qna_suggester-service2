from fastapi import APIRouter, HTTPException
from app.redis_cache import (
    cache_get,
    cache_set,
    async_cache_get_qna_topics,
    async_cache_set_qna_topics
)
from app.pydantic.qna_models import CachedQnAModel
from app.protos import qna_topic_pb2


router = APIRouter(prefix="/redis", tags=["Redis"])


# =====================================================
# 1️⃣ SIMPLE STRING CACHE (quick testing)
# =====================================================
@router.get("/string/get/{key}")
def redis_get_string(key: str):
    """
    Fetch string value from Redis (no protobuf)
    """
    value = cache_get(key)
    return {"key": key, "value": value}


@router.post("/string/set/{key}")
def redis_set_string(key: str, value: dict):
    """
    Store raw string value into Redis (NOT protobuf)
    """
    cache_set(key, str(value))
    return {"status": "stored", "key": key, "value": value}


# =====================================================
# 2️⃣ PROTOBUF CACHE (recommended for real use)
# =====================================================

@router.post("/set/{key}")
async def redis_set_proto(key: str, body: CachedQnAModel):
    """
    Store JSON → protobuf (qna_topic.proto) → Redis
    """

    # Build dictionary structure expected by async_cache_set_qna_topics
    questions_by_topic = {
        topic.topic: {
            "static_questions": topic.static_questions,
            "ai_questions": topic.ai_questions,
            "merged": topic.merged,
        }
        for topic in body.topics
    }

    # Save using async wrapper defined in redis_cache.py
    await async_cache_set_qna_topics(
        key,
        questions_by_topic=questions_by_topic,
        general_tips=body.suggestions
    )

    return {"status": "stored", "key": key}


@router.get("/get/{key}")
async def redis_get_proto(key: str):
    """
    Fetch protobuf bytes from Redis, decode using qna_topic.proto,
    and return as JSON-ready dict.
    """

    decoded = await async_cache_get_qna_topics(key)
    if not decoded:
        raise HTTPException(status_code=404, detail="Key not found")

    return {"key": key, "value": decoded}


# =====================================================
# 3️⃣ HEALTH CHECK
# =====================================================
@router.get("/ping")
def redis_ping():
    return {"status": "ok"}
