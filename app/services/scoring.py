def get_confidence_tier(score: int) -> str:
    if score >= 70:
        return "High"
    elif score >= 45:
        return "Moderate"
    elif score >= 20:
        return "Low"
    else:
        return "Unverified"


def calculate_confidence(cluster_stories: list[dict], original_source: dict) -> dict:
    independent_count = len(cluster_stories) - 1

    breakdown = {
        "independent_confirmations": min(independent_count * 10, 40),
        "early_publication": 15 if original_source.get("published_at") else 0,
        "established_outlet": 20 if original_source.get("source_known") else 0,
        "neutral_language": 10
    }

    total_score = sum(breakdown.values())

    return {
        "score": total_score,
        "tier": get_confidence_tier(total_score),
        "breakdown": breakdown
    }
