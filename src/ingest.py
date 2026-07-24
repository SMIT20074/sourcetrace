import re
import time
import logging
import socket
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import feedparser
from src import database

# Set default socket timeout to 5 seconds so slow feeds don't hang ingestion
socket.setdefaulttimeout(5)

logger = logging.getLogger("sourcetrace.ingest")
logging.basicConfig(level=logging.INFO)

def clean_snippet(raw_text: str) -> str:
    """Removes HTML tags and trims whitespace from summary text."""
    if not raw_text:
        return ""
    cleaned = re.sub(r"<[^>]+>", "", raw_text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
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
    return datetime.now(timezone.utc).isoformat()

def run_ingestion():
    """Fetches all registered sources and ingests their latest RSS stories."""
    print("Starting expanded RSS News Ingestion pipeline (13 feeds)...")
    sources = database.get_all_sources()
    
    if not sources or len(sources) < 10:
        print("[Note]: Seeding new outlets into Supabase...")
        from src.seed_sources import run_seed
        run_seed()
        sources = database.get_all_sources()

    total_ingested = 0

    for source in sources:
        name = source["name"]
        feed_url = source.get("feed_url")
        source_id = source["id"]

        if not feed_url:
            continue

        print(f"\nFetching RSS feed for {name}...")
        try:
            feed = feedparser.parse(feed_url)
            entries = feed.entries or []
            print(f" -> Found {len(entries)} items in {name} feed.")

            for entry in entries[:10]: # Process top 10 stories per outlet
                headline = entry.get("title", "").strip()
                url = entry.get("link", "").strip()
                raw_summary = entry.get("summary") or entry.get("description") or ""
                
                if not headline or not url:
                    continue

                snippet = clean_snippet(raw_summary)
                pub_date = parse_publish_date(entry)

                story_record = database.add_story(
                    source_id=source_id,
                    headline=headline,
                    url=url,
                    snippet=snippet,
                    published_at=pub_date
                )
                total_ingested += 1

        except Exception as e:
            print(f"[Skip {name}]: Feed parsing timeout or error: {e}")

    print(f"\n[COMPLETE] Ingestion finished! Checked/Ingested across {len(sources)} outlets.")

if __name__ == "__main__":
    run_ingestion()
