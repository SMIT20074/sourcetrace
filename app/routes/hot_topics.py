from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from app.services.db import supabase
from app.services.dedup import cluster_stories, rank_by_originality
from app.services.scoring import calculate_confidence

router = APIRouter()


@router.get("/hot-topics")
def get_hot_topics(hours: int = 72, limit: int = 10):
    """
    Automatically detects trending topics by clustering recent stories
    and ranking clusters by how many different outlets covered them.
    No search term needed.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    try:
        response = supabase.table("stories").select("*").gte("published_at", cutoff).limit(300).execute()
    except Exception:
        raise HTTPException(status_code=503, detail="Could not reach the database. Please try again shortly.")

    stories = response.data
    if not stories:
        return {"topics": []}

    clusters = cluster_stories(stories)
    multi_source_clusters = [c for c in clusters if len(c) > 1]
    multi_source_clusters.sort(key=len, reverse=True)

    topics = []
    for cluster in multi_source_clusters[:limit]:
        ranked = rank_by_originality(cluster)
        confidence = calculate_confidence(cluster, ranked["original_source"])
        topics.append({
            "topic_headline": ranked["original_source"]["headline"],
            "outlet_count": len(cluster),
            "confidence": confidence,
            "original_source": ranked["original_source"],
            "syndicated_sources": ranked["syndicated_sources"],
        })

    return {"topics": topics}
