from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.db import supabase
from app.services.cache import get_cached, set_cached

router = APIRouter()

STOPWORDS = {"what", "happened", "with", "the", "about", "does", "did", "have", "has", "this", "that", "who", "when", "where", "why", "how"}


class AskRequest(BaseModel):
    question: str


@router.post("/ask")
def ask_question(request: AskRequest):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    cache_key = f"ask:{request.question.lower().strip()}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    words = [w.strip("?.,!").lower() for w in request.question.split() if len(w) > 3]
    keywords = [w for w in words if w not in STOPWORDS]

    if not keywords:
        result = {
            "answer": "I don't have sufficient verified evidence to answer this.",
            "citations": [],
            "confidence": "none"
        }
        set_cached(cache_key, result)
        return result

    try:
        matched_stories = []
        for word in keywords:
            response = supabase.table("stories").select("*").ilike("headline", f"%{word}%").limit(5).execute()
            matched_stories.extend(response.data)
    except Exception:
        raise HTTPException(status_code=503, detail="Could not reach the database. Please try again shortly.")

    seen_ids = set()
    unique_stories = []
    for story in matched_stories:
        if story["id"] not in seen_ids:
            seen_ids.add(story["id"])
            unique_stories.append(story)

    if not unique_stories:
        result = {
            "answer": "I don't have sufficient verified evidence to answer this.",
            "citations": [],
            "confidence": "none"
        }
        set_cached(cache_key, result)
        return result

    top_matches = unique_stories[:3]
    summary_lines = [f"- {s['headline']} ({s['url']})" for s in top_matches]

    answer = (
        f"Based on {len(top_matches)} verified article(s) in the database, here's what's been reported:\n"
        + "\n".join(summary_lines)
    )

    result = {
        "answer": answer,
        "citations": [{"headline": s["headline"], "url": s["url"]} for s in top_matches],
        "confidence": "based on available verified sources only"
    }

    set_cached(cache_key, result)
    return result
