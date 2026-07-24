def calculate_confidence(cluster_stories: list[dict], original_source: dict) -> dict:
    """
    Calculates a confidence score for a story cluster.
    IMPORTANT: always returns a breakdown of WHY the score is what it is.
    Never return a bare number with no explanation.
    """
    independent_count = len(cluster_stories) - 1  # everyone except the original

    breakdown = {
        "independent_confirmations": min(independent_count * 10, 40),  # capped so volume alone can't inflate the score
        "early_publication": 15 if original_source.get("published_at") else 0,
        "established_outlet": 20 if original_source.get("source_known") else 0,
        "neutral_language": 10  # TODO: replace with real tone/language analysis later
    }

    total_score = sum(breakdown.values())

    return {
        "score": total_score,
        "breakdown": breakdown
    }
