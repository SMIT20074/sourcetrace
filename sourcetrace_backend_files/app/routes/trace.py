from fastapi import APIRouter
from app.services.db import supabase
from app.services.dedup import rank_by_originality
from app.services.scoring import calculate_confidence

router = APIRouter()


@router.get("/trace")
def trace_topic(topic: str):
    response = supabase.table("stories").select("*").ilike("headline", f"%{topic}%").execute()
    stories = response.data

    if not stories:
        return {"message": "No stories found for this topic."}

    ranked = rank_by_originality(stories)
    confidence = calculate_confidence(stories, ranked["original_source"])

    return {
        "original_source": ranked["original_source"],
        "syndicated_sources": ranked["syndicated_sources"],
        "confidence": confidence
    }
