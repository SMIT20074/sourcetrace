from app.services.dedup import compute_similarity, rank_by_originality
from app.services.scoring import calculate_confidence

# Fake data, just to test the logic -- no database needed
fake_stories = [
    {"id": "1", "headline": "ISRO launches new satellite", "snippet": "ISRO successfully launched a satellite today", "published_at": "2026-07-20T09:00:00", "source_known": True},
    {"id": "2", "headline": "India launches satellite via ISRO", "snippet": "ISRO successfully launched a satellite today morning", "published_at": "2026-07-20T09:15:00", "source_known": True},
    {"id": "3", "headline": "Satellite launch confirmed by ISRO", "snippet": "The satellite launch was confirmed successful by ISRO", "published_at": "2026-07-20T09:30:00", "source_known": True},
]

# Test similarity
score = compute_similarity(fake_stories[0]["headline"], fake_stories[1]["headline"])
print("Similarity between story 1 and 2:", score)

# Test originality ranking
ranked = rank_by_originality(fake_stories)
print("\nOriginal source:", ranked["original_source"]["headline"])
print("Syndicated sources:", [s["headline"] for s in ranked["syndicated_sources"]])

# Test confidence scoring
confidence = calculate_confidence(fake_stories, ranked["original_source"])
print("\nConfidence result:", confidence)
