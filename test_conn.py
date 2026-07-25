import sys
from src import database

print("Attempting to connect to Supabase using .env settings...")
try:
    # Attempt to insert a test source into the sources table
    test_src = database.add_source(
        name="Test Ingestion Source",
        feed_url="https://example.com/rss",
        ownership="Test Ownership Group"
    )
    print("\n[SUCCESS] Connected to Supabase!")
    print("Inserted Row ID:", test_src.get("id"))
    print("Source Name:", test_src.get("name"))
except Exception as e:
    print("\n[FAILED] Connection failed!")
    print("Error details:", e)
