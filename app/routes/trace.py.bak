from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from app.services.db import supabase
from app.services.dedup import compute_similarity, rank_by_originality
from app.services.scoring import calculate_confidence
from app.services.cache import get_cached, set_cached

router = APIRouter()

SIMILARITY_THRESHOLD = 0.3
STALE_AFTER_HOURS = 48


@router.get("/trace")
def trace_topic(topic: str):
    if not topic or not topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    cache_key = f"trace:{topic.lower().strip()}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    try:
        response = supabase.table("stories").select("*").ilike("headline", f"%{topic}%").limit(30).execute()
    except Exception:
        raise HTTPException(status_code=503, detail="Could not reach the database. Please try again shortly.")

    candidates = response.data

    if not candidates:
        result = {"message": "No stories found for this topic."}
        set_cached(cache_key, result)
        return result

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

    published_at_str = ranked["original_source"].get("published_at")
    is_stale = False
    hours_since_published = None
    if published_at_str:
        published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        hours_since_published = round((now - published_at).total_seconds() / 3600, 1)
        is_stale = hours_since_published > STALE_AFTER_HOURS

    confidence["staleness"] = {
        "hours_since_published": hours_since_published,
        "is_stale": is_stale,
        "note": "This confidence score may be outdated and hasn't been re-verified recently." if is_stale else "Recently verified."
    }

    url_check = supabase.table("stories").select("*").eq("url", ranked["original_source"]["url"]).execute()
    has_correction = len(url_check.data) > 1 and any(
        s["headline"] != ranked["original_source"]["headline"] for s in url_check.data
    )

    all_sources = supabase.table("sources").select("id, name").execute()
    covering_source_ids = {s["source_id"] for s in real_cluster if s.get("source_id")}
    silent_sources = [s["name"] for s in all_sources.data if s["id"] not in covering_source_ids]

    result = {
        "original_source": ranked["original_source"],
        "syndicated_sources": ranked["syndicated_sources"],
        "confidence": confidence,
        "correction_detected": has_correction,
        "silent_sources": silent_sources,
        "note": "Only articles with meaningfully similar content are counted as confirmations, not just keyword matches. 'silent_sources' lists known outlets in our database that have not covered this specific story."
    }

    set_cached(cache_key, result)
    return result
