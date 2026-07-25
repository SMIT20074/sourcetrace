import logging
from src import database

logger = logging.getLogger("sourcetrace.seed")
logging.basicConfig(level=logging.INFO)

# Initial news outlets registry data
INITIAL_SOURCES = [
    {
        "name": "Times of India",
        "feed_url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "founding_date": "1838-11-03",
        "ownership": "Bennett, Coleman & Co. Ltd. (Times Group)",
        "correction_history": "Publishes formal corrections in print and digital errata sections. Has issued corrections for breaking news attribution errors."
    },
    {
        "name": "NDTV",
        "feed_url": "https://feeds.feedburner.com/ndtvnews-top-stories",
        "founding_date": "1988-11-15",
        "ownership": "AMG Media Networks Limited (Adani Group)",
        "correction_history": "Maintains a digital corrections policy for web reporting and broadcast errata."
    },
    {
        "name": "The Hindu",
        "feed_url": "https://www.thehindu.com/news/feeder/default.rss",
        "founding_date": "1878-09-20",
        "ownership": "The Hindu Group (Kasturi & Sons Ltd.)",
        "correction_history": "Features an official Readers' Editor column and dedicated Corrections & Clarifications policy."
    }
]

def run_seed():
    """Inserts initial news outlets into the Supabase sources table."""
    print("Seeding Source Registry table in Supabase...")
    for outlet in INITIAL_SOURCES:
        try:
            record = database.add_source(
                name=outlet["name"],
                feed_url=outlet["feed_url"],
                founding_date=outlet["founding_date"],
                ownership=outlet["ownership"],
                correction_history=outlet["correction_history"]
            )
            print(f"[SUCCESS] Registered: {record['name']} (ID: {record['id']})")
        except Exception as e:
            print(f"[ERROR] Failed to register {outlet['name']}: {e}")

if __name__ == "__main__":
    run_seed()
