import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve the project root folder (one level above this 'src' folder)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

# Load variables from the .env file if it exists
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# Read variables into Python constants
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

# Print helper status logs (ignoring sensitive keys)
if not SUPABASE_URL or "your-project-id" in SUPABASE_URL:
    print("[Config Warning]: SUPABASE_URL is not set or contains default placeholder values in .env!")
if not SUPABASE_KEY or "your-supabase" in SUPABASE_KEY:
    print("[Config Warning]: SUPABASE_KEY is not set or contains default placeholder values in .env!")
