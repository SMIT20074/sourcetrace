import logging
from src import database

logger = logging.getLogger("sourcetrace.seed")
logging.basicConfig(level=logging.INFO)

# Expanded News Outlets Registry Data (13 Total Outlets)
INITIAL_SOURCES = [
    {
        "name": "Times of India",
        "feed_url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "founding_date": "1838-11-03",
        "ownership": "Bennett, Coleman & Co. Ltd. (Times Group)",
        "correction_history": "Publishes formal corrections in print and digital errata sections."
    },
    {
        "name": "NDTV",
        "feed_url": "https://feeds.feedburner.com/ndtvnews-top-stories",
        "founding_date": "1988-11-15",
        "ownership": "AMG Media Networks Limited (Adani Group)",
        "correction_history": "Maintains a digital corrections policy for web reporting."
    },
    {
        "name": "The Hindu",
        "feed_url": "https://www.thehindu.com/news/feeder/default.rss",
        "founding_date": "1878-09-20",
        "ownership": "The Hindu Group (Kasturi & Sons Ltd.)",
        "correction_history": "Features an official Readers' Editor column and dedicated Corrections policy."
    },
    {
        "name": "Indian Express",
        "feed_url": "https://indianexpress.com/feed/",
        "founding_date": "1932-09-05",
        "ownership": "Express Group (Anant Goenka)",
        "correction_history": "Publishes formal corrections column 'Editor's Note'."
    },
    {
        "name": "Hindustan Times",
        "feed_url": "https://www.hindustantimes.com/feeds/rss/topnews/rssfeed.xml",
        "founding_date": "1924-09-26",
        "ownership": "HT Media Ltd. (Shobhana Bhartia)",
        "correction_history": "Maintains digital corrections and clarifications section."
    },
    {
        "name": "Deccan Herald",
        "feed_url": "https://www.deccanherald.com/rss/top-stories.rss",
        "founding_date": "1948-06-17",
        "ownership": "The Printers (Mysore) Private Limited",
        "correction_history": "Prints daily clarifications and correction notes."
    },
    {
        "name": "Business Standard",
        "feed_url": "https://www.business-standard.com/rss/home_page_top_stories.rss",
        "founding_date": "1975-03-27",
        "ownership": "Business Standard Private Limited (Kotak Family)",
        "correction_history": "Features financial reporting corrections and updates policy."
    },
    {
        "name": "LiveMint",
        "feed_url": "https://www.livemint.com/rss/news",
        "founding_date": "2007-02-01",
        "ownership": "HT Media Ltd.",
        "correction_history": "Digital updates log and disclosure policy."
    },
    {
        "name": "BBC News India",
        "feed_url": "http://feeds.bbci.co.uk/news/world/asia/india/rss.xml",
        "founding_date": "1922-10-18",
        "ownership": "British Broadcasting Corporation (Public Broadcaster)",
        "correction_history": "Public Editorial Guidelines and published Corrections & Clarifications page."
    },
    {
        "name": "Reuters Agency",
        "feed_url": "https://www.reutersagency.com/feed/",
        "founding_date": "1851-10-01",
        "ownership": "Thomson Reuters Corporation",
        "correction_history": "Global News Handbook corrections policy for international wire syndication."
    },
    {
        "name": "Scroll.in",
        "feed_url": "https://scroll.in/feed",
        "founding_date": "2014-01-27",
        "ownership": "Scroll Media Incorporation",
        "correction_history": "Independent digital corrections log."
    },
    {
        "name": "Press Trust of India (PTI)",
        "feed_url": "https://www.ptinews.com/rss/feed",
        "founding_date": "1947-08-27",
        "ownership": "Non-profit News Cooperative owned by Indian Newspapers Consortium",
        "correction_history": "Issues immediate wire corrigendum bulletins to subscribing newsrooms."
    },
    {
        "name": "Asian News International (ANI)",
        "feed_url": "https://www.aninews.in/rss/feed",
        "founding_date": "1971-12-09",
        "ownership": "ANI Media Private Limited (Prem Prakash)",
        "correction_history": "Issues video and text wire advisories for errors."
    }
]

def run_seed():
    """Inserts all 13 news outlets into the Supabase sources table."""
    print("Seeding expanded Source Registry (13 Outlets) in Supabase...")
    count = 0
    for outlet in INITIAL_SOURCES:
        try:
            record = database.add_source(
                name=outlet["name"],
                feed_url=outlet["feed_url"],
                founding_date=outlet["founding_date"],
                ownership=outlet["ownership"],
                correction_history=outlet["correction_history"]
            )
            count += 1
            print(f"[SUCCESS {count}/13] Registered: {record['name']}")
        except Exception as e:
            print(f"[ERROR] Failed to register {outlet['name']}: {e}")

if __name__ == "__main__":
    run_seed()
