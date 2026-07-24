from fastapi import APIRouter, HTTPException
from app.services.db import supabase

router = APIRouter()


@router.get("/stories")
def list_stories():
    response = supabase.table("stories").select("*").limit(20).execute()
    return response.data


@router.get("/stories/{story_id}")
def get_story(story_id: str):
    response = supabase.table("stories").select("*").eq("id", story_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Story not found")
    return response.data[0]
