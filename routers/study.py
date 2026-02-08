"""
Study router - endpoints for studying artists and viewing study data.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import ScrapedSong, ArtistStudy, ArtistRhymeGroup
from library.study import study_song, get_artist_study, get_all_studied_artists

router = APIRouter(prefix="/api/study", tags=["study"])


class LearnRequest(BaseModel):
    scraped_song_id: int


class LearnResponse(BaseModel):
    artist: str
    title: str | None
    endings_added: int
    vocabulary_added: int
    concepts_added: int
    prompts_added: int


@router.get("/artists")
def list_studied_artists(db: Session = Depends(get_db)):
    """List all studied artists with song counts."""
    artists = get_all_studied_artists(db)
    return {"artists": artists}


@router.get("/{artist}")
def get_artist_data(artist: str, db: Session = Depends(get_db)):
    """Get full study data for an artist."""
    study = get_artist_study(artist, db)
    if not study:
        raise HTTPException(status_code=404, detail=f"No study data for artist: {artist}")
    return study


@router.get("/{artist}/rhymes")
def get_artist_rhymes(artist: str, db: Session = Depends(get_db)):
    """Get just rhyme groups for an artist."""
    study = get_artist_study(artist, db)
    if not study:
        raise HTTPException(status_code=404, detail=f"No study data for artist: {artist}")
    return {"artist": artist, "rhyme_groups": study["rhyme_groups"]}


@router.post("/learn", response_model=LearnResponse)
def learn_from_song(request: LearnRequest, db: Session = Depends(get_db)):
    """Study an artist from a scraped song."""
    scraped_song = db.query(ScrapedSong).filter_by(id=request.scraped_song_id).first()
    if not scraped_song:
        raise HTTPException(status_code=404, detail="Scraped song not found")

    result = study_song(scraped_song, db)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return LearnResponse(**result)


@router.delete("/{artist}")
def delete_artist_data(artist: str, db: Session = Depends(get_db)):
    """Delete all data for an artist (songs, study, rhyme groups). Start fresh."""
    # Delete scraped songs for this artist
    songs_deleted = db.query(ScrapedSong).filter(ScrapedSong.artist == artist).delete()

    # Delete artist study
    study_deleted = db.query(ArtistStudy).filter(ArtistStudy.artist == artist).delete()

    # Delete rhyme groups
    groups_deleted = db.query(ArtistRhymeGroup).filter(ArtistRhymeGroup.artist == artist).delete()

    db.commit()

    return {
        "status": "deleted",
        "artist": artist,
        "songs_deleted": songs_deleted,
        "study_deleted": study_deleted,
        "rhyme_groups_deleted": groups_deleted
    }
