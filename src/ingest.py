import re
import time
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import feedparser
from src import database

logger = logging.getLogger("sourcetrace.ingest")
logging.basicConfig(level=logging.INFO)

def clean_snippet(raw_text: str) -> str:
    """Removes HTML tags and trims whitespace from summary text."""
    if not raw_text:
        return ""
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", "", raw_text)
    # Replace multiple whitespace/newlines with a single space
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Cap snippet at 197 characters + "..." to satisfy <= 200 char database constraint
    if len(cleaned) > 200:
        cleaned = cleaned[:197] + "..."
    return cleaned

def parse_publish_date(entry: dict) -> str:
    """Extracts published timestamp and converts it to ISO 8601 string format."""
    raw_date = entry.get("published") or entry.get("updated")
    if raw_date:
        try:
            dt = parsedate_to_datetime(raw_date)
            return dt.isoformat()
        except Exception:
            pass
            
    # Fallback to current timestamp if parsing fails
    return datetime.now(timezone.utc).isoformat()

def run_ingestion():
    """Fetches registered sources and ingests their latest RSS stories."""
    print("Starting RSS News Ingestion pipeline...")
    sources = database.get_all_sources()
    
    if not sources:
        print("[Warning]: No sources found in Supabase. Running seed first...")
        from src.seed_sources import run_seed
        run_seed()
        sources = database.get_all_sources()

    total_ingested = 0

    for source in sources:
        name = source["name"]
        feed_url = source.get("feed_url")
        source_id = source["id"]

        if not feed_url:
            print(f"[Skip]: No RSS feed URL configured for {name}")
            continue

        print(f"\nFetching RSS feed for {name}...")
        try:
            import requests
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            r = requests.get(feed_url, headers=headers, timeout=15)
            feed = feedparser.parse(r.content)
            print(f"Found {len(feed.entries)} items in {name} feed.")

            for entry in feed.entries[:10]: # Process top 10 latest stories per feed
                headline = entry.get("title", "").strip()
                url = entry.get("link", "").strip()
                raw_summary = entry.get("summary") or entry.get("description") or ""
                
                if not headline or not url:
                    continue

                snippet = clean_snippet(raw_summary)
                pub_date = parse_publish_date(entry)

                # Save story to Supabase
                story_record = database.add_story(
                    source_id=source_id,
                    headline=headline,
                    url=url,
                    snippet=snippet,
                    published_at=pub_date
                )
                total_ingested += 1

        except Exception as e:
            print(f"[ERROR] Failed to ingest feed for {name}: {e}")

    print(f"\n[COMPLETE] Ingestion finished! Ingested/Checked {total_ingested} stories.")

if __name__ == "__main__":
    run_ingestion()
