from fastapi import APIRouter
from app.services.db import supabase
from app.services.dedup import compute_similarity, rank_by_originality
from app.services.scoring import calculate_confidence

router = APIRouter()

SIMILARITY_THRESHOLD = 0.3


@router.get("/trace")
def trace_topic(topic: str):
    response = supabase.table("stories").select("*").ilike("headline", f"%{topic}%").execute()
    candidates = response.data

    if not candidates:
        return {"message": "No stories found for this topic."}

    anchor = candidates[0]
    real_cluster = [anchor]
    for story in candidates[1:]:
        score = compute_similarity(
            anchor["headline"] + " " + (anchor.get("snippet") or ""),
            story["headline"] + " " + (story.get("snippet") or "")
        )
        if score >= SIMILARITY_THRESHOLD:
            real_cluster.append(story)

    ranked = rank_by_originality(real_cluster)
    confidence = calculate_confidence(real_cluster, ranked["original_source"])

    return {
        "original_source": ranked["original_source"],
        "syndicated_sources": ranked["syndicated_sources"],
        "confidence": confidence,
        "note": "Only articles with meaningfully similar content are counted as confirmations, not just keyword matches."
    }
