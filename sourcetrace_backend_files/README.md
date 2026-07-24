# How to use this

1. Unzip this folder.
2. Copy EVERYTHING inside it directly into your `sourcetrace-backend` folder
   (the one you already made on your Desktop), overwriting the empty files
   you created earlier.
3. Rename `.env.example` to `.env` (or copy its contents into your existing `.env`),
   then paste your real Supabase URL + key into it.
4. Open Terminal, go to your project folder, and make sure your venv is active:

```bash
cd ~/Desktop/sourcetrace-backend
source venv/bin/activate
```

5. Test the logic WITHOUT needing Supabase yet:

```bash
python3 test_dedup.py
```

You should see similarity scores, an original source, syndicated sources, and a
confidence breakdown printed out. If this works, your scoring/dedup logic is correct.

6. Once you have real Supabase credentials in `.env`, run the actual server:

```bash
uvicorn app.main:app --reload
```

Then visit `http://localhost:8000/docs` in your browser to see and test your API.

## What's in here
- `app/main.py` — starts the app, wires all routes together
- `app/config.py` — reads your `.env` secrets
- `app/services/db.py` — connects to Supabase
- `app/services/dedup.py` — similarity + originality logic
- `app/services/scoring.py` — confidence score with explanation breakdown
- `app/routes/health.py`, `stories.py`, `trace.py` — your API endpoints
- `test_dedup.py` — test everything with fake data, no database needed
