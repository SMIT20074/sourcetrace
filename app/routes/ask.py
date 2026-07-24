from fastapi import APIRouter
from pydantic import BaseModel
from app.services.db import supabase

router = APIRouter()

STOPWORDS = {"what", "happened", "with", "the", "about", "does", "did", "have", "has", "this", "that", "who", "when", "where", "why", "how"}


class AskRequest(BaseModel):
    question: str


@router.post("/ask")
def ask_question(request: AskRequest):
    words = [w.strip("?.,!").lower() for w in request.question.split() if len(w) > 3]
    keywords = [w for w in words if w not in STOPWORDS]

    matched_stories = []
    for word in keywords:
        response = supabase.table("stories").select("*").ilike("headline", f"%{word}%").limit(5).execute()
        matched_stories.extend(response.data)

    seen_ids = set()
    unique_stories = []
    for story in matched_stories:
        if story["id"] not in seen_ids:
            seen_ids.add(story["id"])
            unique_stories.append(story)

    if not unique_stories:
        return {
            "answer": "I don't have sufficient verified evidence to answer this.",
            "citations": [],
            "confidence": "none"
        }

    top_matches = unique_stories[:3]
    summary_lines = [f"- {s['headline']} ({s['url']})" for s in top_matches]

    answer = (
        f"Based on {len(top_matches)} verified article(s) in the database, here's what's been reported:\n"
        + "\n".join(summary_lines)
    )

    return {
        "answer": answer,
        "citations": [{"headline": s["headline"], "url": s["url"]} for s in top_matches],
        "confidence": "based on available verified sources only"
    }
