from fastapi import APIRouter
from app.services import db, redis_store

router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    checks = {
        "ok": True,
        "db": db.ping(),
        "redis": redis_store.ping(),
    }
    return checks
