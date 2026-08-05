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
        "first_observed_source": original,
        "syndicated_sources": copies
    }


def cluster_stories(stories: list[dict], threshold: float = 0.75) -> list[list[dict]]:
    """
    Groups a list of stories into clusters about the same real-world event.
    Builds one TF-IDF matrix for all stories up front and computes all
    pairwise similarities in a single matrix operation, instead of
    re-fitting a new model for every pair. Much faster on larger batches,
    like the Hot Topics feed.
    """
    if not stories:
        return []

    texts = [story["headline"] + " " + (story.get("snippet") or "") for story in stories]

    if len(stories) == 1:
        return [[stories[0]]]

    vectorizer = TfidfVectorizer().fit(texts)
    vectors = vectorizer.transform(texts)
    similarity_matrix = cosine_similarity(vectors)

    assigned = [False] * len(stories)
    clusters: list[list[dict]] = []

    for i in range(len(stories)):
        if assigned[i]:
            continue
        cluster = [stories[i]]
        assigned[i] = True
        for j in range(i + 1, len(stories)):
            if not assigned[j] and similarity_matrix[i][j] >= threshold:
                cluster.append(stories[j])
                assigned[j] = True
        clusters.append(cluster)

    return clusters


SYNDICATION_SIMILARITY_THRESHOLD = 0.85


def is_cross_outlet_syndication(article: dict, reference: dict, threshold: float = SYNDICATION_SIMILARITY_THRESHOLD) -> bool:
    """
    Returns True if `article` is a near-identical copy of `reference`'s content
    (e.g. both republishing the same wire story), even though they're from
    different domains/outlets. This catches syndicated wire content that a
    same-domain-only check would miss.
    """
    sim = compute_similarity(
        reference.get("headline", "") + " " + (reference.get("snippet") or ""),
        article.get("headline", "") + " " + (article.get("snippet") or "")
    )
    return sim >= threshold
