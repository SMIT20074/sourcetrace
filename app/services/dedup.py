from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def compute_similarity(text_a: str, text_b: str) -> float:
    """
    Compares two pieces of text and returns a similarity score between 0 and 1.
    Closer to 1 = very similar text (likely copied/syndicated).
    Closer to 0 = unrelated.
    """
    vectorizer = TfidfVectorizer().fit([text_a, text_b])
    vectors = vectorizer.transform([text_a, text_b])
    similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
    return float(similarity)


def find_cluster(new_story: dict, existing_stories: list[dict], threshold: float = 0.75) -> str | None:
    """
    Checks a new story against existing stories to see if it belongs to
    an existing cluster (same real-world event). Returns the cluster_id
    if a match is found, or None if this is a new event.
    """
    for story in existing_stories:
        score = compute_similarity(
            new_story["headline"] + " " + new_story["snippet"],
            story["headline"] + " " + story["snippet"]
        )
        if score >= threshold:
            return story.get("cluster_id")
    return None


def rank_by_originality(cluster_stories: list[dict]) -> dict:
    """
    Given a group of stories about the same event, sorts them by
    publish time to determine which one was first (original) and
    which ones came after (syndicated/copied).
    """
    sorted_stories = sorted(cluster_stories, key=lambda s: s["published_at"])
    original = sorted_stories[0]
    copies = sorted_stories[1:]
    return {
        "original_source": original,
        "syndicated_sources": copies
    }
