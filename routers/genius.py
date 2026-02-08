from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from library.genius_api import search_artists, get_artist_songs, get_song_details

router = APIRouter(prefix="/api/genius", tags=["genius"])


@router.get("/search/artists")
def search_artists_endpoint(q: str, limit: int = 10):
    """Search for artists by name."""
    try:
        artists = search_artists(q, limit)
        return {"artists": artists}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/artists/{artist_id}/songs")
def get_artist_songs_endpoint(artist_id: int, limit: int = 50):
    """Get all songs by an artist."""
    try:
        songs = get_artist_songs(artist_id, limit)
        return {"songs": songs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/songs/{song_id}")
def get_song_details_endpoint(song_id: int):
    """Get details about a specific song."""
    try:
        song = get_song_details(song_id)
        return song
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
