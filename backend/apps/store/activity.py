import logging
from django.conf import settings
logger = logging.getLogger(__name__)
def log_activity(event_type, *, user_id=None, product_id=None, query=None, metadata=None):
    """Best-effort Mongo event log. Never pass secrets or personal/payment data here."""
    if not settings.MONGO_ENABLED:
        return False
    try:
        from pymongo import MongoClient
        with MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=700) as client:
            client[settings.MONGO_DATABASE]["activity_events"].insert_one({
                "event_type": str(event_type)[:40],
                "user_id": str(user_id) if user_id else None,
                "product_id": str(product_id) if product_id else None,
                "query": str(query)[:200] if query else None,
                "metadata": metadata or {},
            })
        return True
    except Exception:
        logger.warning("MongoDB activity logging unavailable; continuing request.", exc_info=True)
        return False
