def get_confidence_tier(score: int) -> str:
    if score >= 70:
        return "High"
    elif score >= 45:
        return "Moderate"
    elif score >= 20:
        return "Low"
    else:
        return "Unverified"


def get_claim_type(headline: str, snippet: str = "") -> str:
    """
    Assigns a neutral, rule-based claim_type classification tag (Fact, Disputed, Allegation, Opinion)
    based on keyword patterns in headline and snippet.
    """
    text = f"{headline} {snippet}".lower()
    if any(k in text for k in ["op-ed", "opinion", "column", "editorial", "perspective", "view:"]):
        return "Opinion"
    elif any(k in text for k in ["alleged", "allegation", "accused", "claims", "charged", "reportedly", "suspected"]):
        return "Allegation"
    elif any(k in text for k in ["disputed", "denies", "rejected", "contested", "refutes", "clash"]):
        return "Disputed"
    else:
        return "Fact"


def calculate_confidence(cluster_stories: list[dict], first_observed_source: dict) -> dict:
    independent_count = max(0, len(cluster_stories) - 1)

    # 4 Reframed Component Scores matching Build Plan:
    source_track_record = 20 if (first_observed_source.get("source_id") or first_observed_source.get("publisher")) else 10
    cross_verification = min(independent_count * 10, 40)
    framing_difference = 10
    originality = 15 if first_observed_source.get("published_at") else 0

    breakdown = {
        "source_track_record": source_track_record,
        "cross_verification": cross_verification,
        "framing_difference": framing_difference,
        "originality": originality,
    }

    total_score = sum(breakdown.values())
    claim_type = get_claim_type(
        first_observed_source.get("headline", ""),
        first_observed_source.get("snippet", "")
    )

    return {
        "score": total_score,
        "tier": get_confidence_tier(total_score),
        "claim_type": claim_type,
        "breakdown": breakdown
    }

