import os
import redis
from dotenv import load_dotenv
from app.protos import qna_topic_pb2

load_dotenv()

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    username=os.getenv("REDIS_USERNAME"),
    password=os.getenv("REDIS_PASSWORD"),
    ssl=False,
    ssl_cert_reqs=None
)

# ==============================================================
# STRING CACHE
# ==============================================================

def cache_set(key: str, value: str):
    redis_client.set(key, value)


def cache_get(key: str):
    value = redis_client.get(key)
    return value.decode("utf-8") if value else None


# ==============================================================
# PROTOBUF CACHE
# ==============================================================

def cache_set_qna_topics(key: str, questions_by_topic: dict, general_tips: list[str]):
    pb = qna_topic_pb2.CachedQnA()

    for topic_name, data in questions_by_topic.items():
        entry = pb.topics.add()
        entry.topic = topic_name

        entry.static_questions.extend(data.get("static_questions", []))
        entry.ai_questions.extend(data.get("ai_questions", []))
        entry.merged.extend(data.get("merged", []))

    pb.suggestions.extend(general_tips)

    # 👉 No expiry
    redis_client.set(key, pb.SerializeToString())


def cache_get_qna_topics(key: str):
    raw = redis_client.get(key)
    if not raw:
        return None

    pb = qna_topic_pb2.CachedQnA()
    pb.ParseFromString(raw)

    out = {
        "topics": {},
        "suggestions": list(pb.suggestions),
    }

    for entry in pb.topics:
        out["topics"][entry.topic] = {
            "static_questions": list(entry.static_questions),
            "ai_questions": list(entry.ai_questions),
            "merged": list(entry.merged),
        }

    return out


# ==============================================================
# ASYNC WRAPPERS (UPDATED: NO TTL)
# ==============================================================

async def async_cache_set_qna_topics(key: str, questions_by_topic: dict, general_tips: list[str]):
    cache_set_qna_topics(key, questions_by_topic, general_tips)


async def async_cache_get_qna_topics(key: str):
    return cache_get_qna_topics(key)



# UTILITIES


def cache_delete(key: str):
    redis_client.delete(key)


def cache_flush():
    redis_client.flushdb()
