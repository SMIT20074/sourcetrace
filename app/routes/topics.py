from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from app.services.db import supabase
from app.services.dedup import compute_similarity, cluster_stories, rank_by_originality, is_cross_outlet_syndication
from app.services.scoring import calculate_confidence
from app.services.cache import get_cached, set_cached

router = APIRouter()

TOPIC_MATCH_THRESHOLD = 0.05
CLUSTER_SIMILARITY_THRESHOLD = 0.35


@router.get("/topics/search")
def search_topics(topic: str, hours: int = 168):
    """
    Searches for news clusters related to a given topic within the
    specified time window (default 7 days / 168 hours).

    Returns all matching event clusters with their articles, the earliest
    observed source per cluster, corroborating source counts, and an
    AI-free summary derived directly from article data.
    """
    if not topic or not topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    cache_key = f"topics_search:{topic.lower().strip()}:{hours}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    try:
        response = (
            supabase.table("stories")
            .select("*")
            .gte("published_at", cutoff)
            .limit(500)
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not reach the database. Please try again shortly.",
        )

    all_stories = response.data

    if not all_stories:
        result = {
            "status": "ok",
            "clusters": [],
            "diagnostics": {
                "reason": "no_stories_in_window",
                "message": f"No stories were ingested in the last {hours} hours.",
            },
        }
        set_cached(cache_key, result)
        return result

    # Score every story against the topic query
    scored = []
    for story in all_stories:
        score = compute_similarity(
            topic,
            story["headline"] + " " + (story.get("snippet") or ""),
        )
        scored.append((score, story))

    scored.sort(key=lambda pair: pair[0], reverse=True)

    # Filter stories that are meaningfully related to the topic
    relevant = [story for score, story in scored if score >= TOPIC_MATCH_THRESHOLD]

    if not relevant:
        result = {
            "status": "ok",
            "clusters": [],
            "diagnostics": {
                "reason": "no_topic_match",
                "message": (
                    f"Stories exist in the last {hours} hours, but none matched "
                    f"the topic '{topic}' above the relevance threshold."
                ),
            },
        }
        set_cached(cache_key, result)
        return result

    # Load registered sources metadata lookup map
    try:
        sources_res = supabase.table("sources").select("*").execute()
        sources_by_id = {s["id"]: s for s in sources_res.data} if sources_res.data else {}
        sources_by_name = {s["name"].lower(): s for s in sources_res.data} if sources_res.data else {}
    except Exception:
        sources_by_id, sources_by_name = {}, {}

    # Cluster the relevant stories into distinct real-world events
    raw_clusters = cluster_stories(relevant, threshold=CLUSTER_SIMILARITY_THRESHOLD)

    clusters_out = []
    for cluster in raw_clusters:
        if not cluster:
            continue

        ranked = rank_by_originality(cluster)
        first_observed = ranked["first_observed_source"]
        corroborating = ranked["syndicated_sources"]
        confidence = calculate_confidence(cluster, first_observed)

        first_domain = _domain(first_observed.get("url", ""))

        # Build the article list with relation_to_cluster & source credibility metadata
        articles = []
        for article in [first_observed] + corroborating:
            art_domain = _domain(article.get("url", ""))
            pub_name = article.get("publisher") or art_domain

            if article is first_observed:
                rel = "first_observed_source"
                rel_label = "First Observed in SourceTrace"
            elif art_domain and art_domain == first_domain:
                rel = "syndicated_copy"
                rel_label = "Syndicated Copy"
            elif is_cross_outlet_syndication(article, first_observed):
                # Different outlet, but near-identical content (e.g. same wire story) -- still a copy, not a real confirmation.
                rel = "syndicated_copy"
                rel_label = "Syndicated Copy"
            else:
                rel = "independent_confirmation"
                rel_label = "Independent Confirmation"

            # Lookup source credibility facts
            src_info = {}
            sid = article.get("source_id")
            if sid and sid in sources_by_id:
                s = sources_by_id[sid]
                src_info = {
                    "founding_date": s.get("founding_date"),
                    "ownership": s.get("ownership"),
                    "correction_history": s.get("correction_history"),
                }
            elif pub_name.lower() in sources_by_name:
                s = sources_by_name[pub_name.lower()]
                src_info = {
                    "founding_date": s.get("founding_date"),
                    "ownership": s.get("ownership"),
                    "correction_history": s.get("correction_history"),
                }

            articles.append({
                "headline": article.get("headline", ""),
                "url": article.get("url", ""),
                "publisher": pub_name,
                "published_at": article.get("published_at", ""),
                "snippet": article.get("snippet", ""),
                "is_first_observed": article is first_observed,
                "relation_to_cluster": rel,
                "relation_label": rel_label,
                "source_metadata": src_info,
            })

        clusters_out.append({
            "event_title": first_observed.get("headline", ""),
            "corroborating_source_count": len(corroborating),
            "confidence": confidence,
            "first_observed_source": {
                "headline": first_observed.get("headline", ""),
                "url": first_observed.get("url", ""),
                "publisher": first_observed.get("publisher") or first_domain,
                "published_at": first_observed.get("published_at", ""),
                "snippet": first_observed.get("snippet", ""),
            },
            "articles": articles,
        })

    result = {"status": "ok", "clusters": clusters_out}
    set_cached(cache_key, result)
    return result


def _domain(url: str) -> str:
    """Extracts a readable domain name from a URL."""
    if not url:
        return "Unknown Source"
    try:
        from urllib.parse import urlparse
        hostname = urlparse(url).hostname or ""
        return hostname.replace("www.", "")
    except Exception:
        return "Unknown Source"
