import json
import os
from app.redis_cache import redis_client, cache_set_qna_topics
from app.protos import qna_topic_pb2

DATASET_PATH = os.path.join(os.path.dirname(__file__), "data", "qna_dataset.json")


def preload_dataset():
    print(" Preloading QnA dataset into Redis...")

    if not os.path.exists(DATASET_PATH):
        print(f" Dataset not found at: {DATASET_PATH}")
        return

    # Load the saved JSON dataset
    with open(DATASET_PATH, "r") as f:
        dataset = json.load(f)

    # Iterate each topic
    for topic_name, data in dataset.items():

        key = f"qna:{topic_name.lower().replace(' ', '_')}"   # e.g., qna:data_structures

        questions_by_topic = {
            topic_name: {
                "static_questions": data.get("static_questions", []),
                "ai_questions": data.get("ai_questions", []),
                "merged": list(dict.fromkeys(data.get("static_questions", []) + data.get("ai_questions", [])))
            }
        }

        general_tips = ["Be confident", "Explain your reasoning clearly"]

        # Store to Redis
        cache_set_qna_topics(key, questions_by_topic, general_tips)

        print(f" Loaded topic: {topic_name}  → Redis key: {key}")

    print(" All topics successfully preloaded into Redis!")
