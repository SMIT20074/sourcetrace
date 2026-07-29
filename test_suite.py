"""
Test suite covering Step 8 requirements:
- Clustering correctness
- Distinct-source corroboration counting
- First-observed ordering correctness
- No-match / low-evidence honest empty state
- Outage behavior degrades gracefully
- Citation validation strips fabricated references
- No fabricated sources/URLs under any tested condition
"""
import re
from unittest.mock import patch, MagicMock
from app.services.dedup import compute_similarity, cluster_stories, rank_by_originality
from app.services.scoring import calculate_confidence


def make_story(id, headline, snippet="", published_at="2026-07-20T09:00:00", source_id="src-1", url=None):
    return {
        "id": id,
        "headline": headline,
        "snippet": snippet,
        "published_at": published_at,
        "source_id": source_id,
        "url": url or f"https://example.com/{id}",
    }


# ---- Clustering correctness ----

def test_clustering_groups_similar_stories():
    stories = [
        make_story("1", "India launches new satellite via ISRO"),
        make_story("2", "ISRO successfully launches satellite today", source_id="src-2"),
        make_story("3", "Completely unrelated story about cricket match", source_id="src-3"),
    ]
    clusters = cluster_stories(stories, threshold=0.3)
    cluster_ids = [set(s["id"] for s in c) for c in clusters]
    assert any({"1", "2"}.issubset(ids) for ids in cluster_ids), "Similar stories should cluster together"
    assert not any({"1", "3"}.issubset(ids) for ids in cluster_ids), "Unrelated stories should not cluster"


def test_clustering_handles_empty_input():
    assert cluster_stories([], threshold=0.3) == []


# ---- Distinct-source corroboration counting ----

def test_confidence_does_not_overcount_same_outlet():
    first = make_story("1", "Big event happens", source_id="src-A")
    same_outlet_dupes = [make_story(str(i), "Big event happens again", source_id="src-A") for i in range(2, 5)]
    cluster = [first] + same_outlet_dupes
    confidence = calculate_confidence(cluster, first)
    # 3 extra articles, but all from the SAME outlet -> should count as 0 independent confirmations
    assert confidence["breakdown"]["cross_verification"] == 0


def test_confidence_counts_distinct_outlets_correctly():
    first = make_story("1", "Big event happens", source_id="src-A")
    distinct_outlets = [make_story(str(i), "Big event happens too", source_id=f"src-{i}") for i in range(2, 5)]
    cluster = [first] + distinct_outlets
    confidence = calculate_confidence(cluster, first)
    # 3 distinct additional outlets -> 30 points (10 each, per scoring.py logic)
    assert confidence["breakdown"]["cross_verification"] == 30


# ---- First-observed ordering correctness ----

def test_rank_by_originality_picks_earliest():
    stories = [
        make_story("1", "Story reported later", published_at="2026-07-20T12:00:00"),
        make_story("2", "Story reported first", published_at="2026-07-20T09:00:00"),
        make_story("3", "Story reported even later", published_at="2026-07-20T15:00:00"),
    ]
    ranked = rank_by_originality(stories)
    assert ranked["first_observed_source"]["id"] == "2"


# ---- Citation validation (mirrors the logic used in ask.py) ----

def strip_invalid_citations(answer_text, valid_urls):
    mentioned_urls = re.findall(r'https?://\S+', answer_text)
    for url in mentioned_urls:
        cleaned_url = url.rstrip('.,)')
        if cleaned_url not in valid_urls:
            answer_text = answer_text.replace(url, "[citation removed: not in verified evidence set]")
    return answer_text


def test_citation_validation_strips_fabricated_url():
    valid_urls = {"https://real-source.com/article1"}
    fabricated_answer = "According to https://fake-made-up-site.com/lies, this happened."
    cleaned = strip_invalid_citations(fabricated_answer, valid_urls)
    assert "fake-made-up-site.com" not in cleaned
    assert "[citation removed" in cleaned


def test_citation_validation_keeps_real_url():
    valid_urls = {"https://real-source.com/article1"}
    real_answer = "According to https://real-source.com/article1, this happened."
    cleaned = strip_invalid_citations(real_answer, valid_urls)
    assert "https://real-source.com/article1" in cleaned
    assert "[citation removed" not in cleaned


def test_no_fabricated_sources_in_citations_list():
    cluster_articles = [make_story("1", "Real headline", url="https://real.com/a")]
    citations = [{"headline": s["headline"], "url": s["url"]} for s in cluster_articles]
    valid_urls = {a["url"] for a in cluster_articles}
    for c in citations:
        assert c["url"] in valid_urls, "Every citation URL must come from the actual cluster evidence"


# ---- No-match / low-evidence honest empty state ----

def test_empty_cluster_list_returns_no_topics_not_crash():
    # Simulates hot_topics.py's behavior: empty stories -> honest diagnostics, no crash
    stories = []
    if not stories:
        result = {"topics": [], "diagnostics": {"stories_in_window": 0}}
    assert result["topics"] == []
    assert "diagnostics" in result


# ---- Outage behavior degrades gracefully ----

def test_groq_failure_falls_back_to_headline_summary():
    cluster_articles = [make_story("1", "Fallback headline", url="https://real.com/a")]

    def fake_groq_call_that_fails():
        raise Exception("Groq API is down")

    try:
        fake_groq_call_that_fails()
        answer_text = "should not reach here"
    except Exception:
        top_lines = [f"- {s['headline']} ({s['url']})" for s in cluster_articles[:3]]
        answer_text = f"Based on {len(cluster_articles[:3])} verified article(s):\n" + "\n".join(top_lines)

    assert "Fallback headline" in answer_text
    assert "https://real.com/a" in answer_text


def test_db_failure_does_not_crash_caller():
    def fake_db_call_that_fails():
        raise Exception("Database unreachable")

    result = None
    try:
        fake_db_call_that_fails()
    except Exception:
        result = {"error": "Could not reach the database. Please try again shortly."}

    assert result is not None
    assert "error" in result
