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
    },
{
        "name": "Hindustan Times",
        "feed_url": "https://www.hindustantimes.com/rss/topnews/rssfeed.xml",
        "founding_date": "1924-09-26",
        "ownership": "HT Media Ltd. (KK Birla family)",
        "correction_history": "Maintains an editorial corrections policy for factual errors in print and digital reporting."
    },
    {
        "name": "Indian Express",
        "feed_url": "https://indianexpress.com/section/india/feed/",
        "founding_date": "1932-01-01",
        "ownership": "The Indian Express Group",
        "correction_history": "Publishes corrections and clarifications through its editorial standards desk."
    },
    {
        "name": "India Today",
        "feed_url": "https://www.indiatoday.in/rss/1206584",
        "founding_date": "1975-12-01",
        "ownership": "Living Media India Ltd. (India Today Group)",
        "correction_history": "Maintains a corrections policy for digital and broadcast reporting errors."
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
