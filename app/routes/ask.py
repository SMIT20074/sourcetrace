from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from groq import Groq
from app.services.db import supabase
from app.services.cache import get_cached, set_cached
from app.config import GROQ_API_KEY

router = APIRouter()
client = Groq(api_key=GROQ_API_KEY)

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
        result = {"answer": "I don't have sufficient verified evidence to answer this.", "citations": [], "confidence": "none"}
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
        result = {"answer": "I don't have sufficient verified evidence to answer this.", "citations": [], "confidence": "none"}
        set_cached(cache_key, result)
        return result

    top_matches = unique_stories[:5]
    context_blocks = []
    for i, s in enumerate(top_matches):
        context_blocks.append(f"[Article {i+1}]\nHeadline: {s['headline']}\nSnippet: {s.get('snippet', '')}\nPublished: {s.get('published_at', '')}")
    context_text = "\n\n".join(context_blocks)

    prompt = f"""You are answering a question using ONLY the verified articles provided below.

STRICT RULES:
- Use ONLY the information in the articles below. Do not use any outside knowledge.
- If the articles do not contain enough information to answer the question, say exactly: "I don't have sufficient verified evidence to answer this."
- Never speculate, guess, or fill in gaps with assumptions.
- Do not call anything "true" or "false" -- only describe what the articles report.
- Keep the answer concise (2-4 sentences).

VERIFIED ARTICLES:
{context_text}

QUESTION: {request.question}

ANSWER:"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300
        )
        answer_text = completion.choices[0].message.content.strip()
    except Exception:
        top_lines = [f"- {s['headline']} ({s['url']})" for s in top_matches[:3]]
        answer_text = f"Based on {len(top_matches[:3])} verified article(s):\n" + "\n".join(top_lines)

    result = {
        "answer": answer_text,
        "citations": [{"headline": s["headline"], "url": s["url"]} for s in top_matches],
        "confidence": "based on available verified sources only"
    }
    set_cached(cache_key, result)
    return result
