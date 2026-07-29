from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from groq import Groq
import re
from app.services.db import supabase
from app.services.cache import get_cached, set_cached
from app.services.dedup import compute_similarity, cluster_stories, rank_by_originality
from app.config import GROQ_API_KEY

router = APIRouter()
client = Groq(api_key=GROQ_API_KEY)

TOPIC_MATCH_THRESHOLD = 0.05
CLUSTER_SIMILARITY_THRESHOLD = 0.35


class AskRequest(BaseModel):
    question: str


def _no_evidence_result():
    return {
        "answer": "I don't have sufficient verified evidence to answer this.",
        "citations": [],
        "confidence": "no evidence available",
    }


@router.post("/ask")
def ask_question(request: AskRequest):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    cache_key = f"ask:{request.question.lower().strip()}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    try:
        response = supabase.table("stories").select("*").order("published_at", desc=True).limit(300).execute()
    except Exception:
        raise HTTPException(status_code=503, detail="Could not reach the database. Please try again shortly.")

    all_stories = response.data
    if not all_stories:
        result = _no_evidence_result()
        set_cached(cache_key, result)
        return result

    scored = []
    for story in all_stories:
        score = compute_similarity(
            request.question,
            story["headline"] + " " + (story.get("snippet") or ""),
        )
        scored.append((score, story))

    relevant = [story for score, story in scored if score >= TOPIC_MATCH_THRESHOLD]
    if not relevant:
        result = _no_evidence_result()
        set_cached(cache_key, result)
        return result

    raw_clusters = cluster_stories(relevant, threshold=CLUSTER_SIMILARITY_THRESHOLD)
    raw_clusters = [c for c in raw_clusters if c]
    if not raw_clusters:
        result = _no_evidence_result()
        set_cached(cache_key, result)
        return result

    scored_by_id = {story["id"]: score for score, story in scored}
    best_cluster = max(
        raw_clusters,
        key=lambda cluster: max(scored_by_id.get(s["id"], 0) for s in cluster)
    )

    ranked = rank_by_originality(best_cluster)
    first_observed = ranked["first_observed_source"]
    cluster_articles = [first_observed] + ranked["syndicated_sources"]

    valid_urls = {a["url"] for a in cluster_articles if a.get("url")}

    context_blocks = []
    for i, s in enumerate(cluster_articles):
        context_blocks.append(
            f"[Article {i+1}] (id: {s.get('id','')})\n"
            f"Headline: {s['headline']}\n"
            f"Snippet: {s.get('snippet', '')}\n"
            f"Published: {s.get('published_at', '')}"
        )
    context_text = "\n\n".join(context_blocks)

    prompt = f"""You are answering a question using ONLY the verified articles provided below, which are all part of the SAME resolved story cluster.

STRICT RULES:
- Use ONLY the information in the articles below. Do not use any outside knowledge.
- If the articles do not contain enough information to answer the question, say exactly: "I don't have sufficient verified evidence to answer this."
- Never speculate, guess, or fill in gaps with assumptions.
- Do not call anything "true" or "false" -- only describe what the articles report.
- Refer to the earliest article as "first observed in SourceTrace" -- never call it the "original source."
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
        top_lines = [f"- {s['headline']} ({s['url']})" for s in cluster_articles[:3]]
        answer_text = f"Based on {len(cluster_articles[:3])} verified article(s):\n" + "\n".join(top_lines)

    mentioned_urls = re.findall(r'https?://\S+', answer_text)
    for url in mentioned_urls:
        cleaned_url = url.rstrip('.,)')
        if cleaned_url not in valid_urls:
            answer_text = answer_text.replace(url, "[citation removed: not in verified evidence set]")

    result = {
        "answer": answer_text,
        "citations": [{"headline": s["headline"], "url": s["url"]} for s in cluster_articles],
        "confidence": "based on available verified sources only"
    }
    set_cached(cache_key, result)
    return result
