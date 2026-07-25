import logging
from typing import Any, Dict, List, Optional
from supabase import create_client, Client
from src import config

logger = logging.getLogger("sourcetrace.database")

# Initialize the global Supabase Client
supabase: Optional[Client] = None

if config.SUPABASE_URL and config.SUPABASE_KEY:
    try:
        supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        logger.info("Supabase client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
else:
    logger.warning("Supabase URL or Key is missing. Database commands will fail.")

def get_client() -> Client:
    """Returns the active Supabase client. Throws error if not connected."""
    if supabase is None:
        raise ValueError("Supabase client is not connected. Please verify your .env file keys.")
    return supabase

def add_source(
    name: str, 
    feed_url: Optional[str] = None, 
    founding_date: Optional[str] = None, 
    ownership: Optional[str] = None, 
    correction_history: Optional[str] = None
) -> Dict[str, Any]:
    """
    Inserts an news outlet into the 'sources' table.
    If a source with the same name already exists, returns the existing record.
    """
    client = get_client()
    
    # Check if this outlet is already registered
    existing = client.table("sources").select("*").eq("name", name).execute()
    if existing.data:
        return existing.data[0]
        
    # Prepare data payload
    data = {
        "name": name,
        "feed_url": feed_url,
        "founding_date": founding_date,
        "ownership": ownership,
        "correction_history": correction_history
    }
    
    # Strip out None values so database defaults (like default timestamps) trigger correctly
    cleaned_data = {k: v for k, v in data.items() if v is not None}
    
    response = client.table("sources").insert(cleaned_data).execute()
    logger.info(f"Registered source: {name}")
    return response.data[0]

def add_story(
    source_id: str, 
    headline: str, 
    url: str, 
    snippet: Optional[str], 
    published_at: str
) -> Dict[str, Any]:
    """
    Inserts an article into the 'stories' table.
    Caps the snippet at 200 characters to comply with legal/copyright constraints.
    """
    client = get_client()
    
    # Check if the article URL has already been ingested
    existing = client.table("stories").select("*").eq("url", url).execute()
    if existing.data:
        logger.info(f"Story already exists: {url}")
        return existing.data[0]
        
    # Enforce 200 character cap on snippet to prevent SQL Check errors
    if snippet and len(snippet) > 200:
        snippet = snippet[:197] + "..."
        
    data = {
        "source_id": source_id,
        "headline": headline,
        "url": url,
        "snippet": snippet,
        "published_at": published_at
    }
    
    response = client.table("stories").insert(data).execute()
    logger.info(f"Ingested story: {headline}")
    return response.data[0]

def get_all_sources() -> List[Dict[str, Any]]:
    """Retrieves all registered news outlets."""
    client = get_client()
    response = client.table("sources").select("*").execute()
    return response.data
