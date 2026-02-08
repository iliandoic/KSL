import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db, engine
from database.models import ScrapedSong
from library.genius_api import get_song_id_from_url, get_song_details
from sqlalchemy import text

router = APIRouter(prefix="/api/scraped", tags=["scraped"])


@router.post("/migrate")
def run_migration():
    """Add missing columns to scraped_songs table."""
    migrations = [
        "ALTER TABLE scraped_songs ADD COLUMN IF NOT EXISTS primary_artist VARCHAR(200)",
        "ALTER TABLE scraped_songs ADD COLUMN IF NOT EXISTS primary_artist_image VARCHAR(500)",
        "ALTER TABLE scraped_songs ADD COLUMN IF NOT EXISTS featured_artists_json TEXT",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
            except Exception as e:
                pass  # Column might already exist
        conn.commit()
    return {"status": "migrated"}


class SaveScrapedRequest(BaseModel):
    title: str
    artist: str
    url: str
    original_text: str
    sections: list
    sonnet_translations: dict
    opus_translations: dict


class UpdateTranslationsRequest(BaseModel):
    sonnet_translations: dict | None = None
    opus_translations: dict | None = None


@router.post("/save")
def save_scraped(req: SaveScrapedRequest, db: Session = Depends(get_db)):
    """Save a scraped song with its translations."""
    # Check if URL already exists
    existing = db.query(ScrapedSong).filter(ScrapedSong.url == req.url).first()

    if existing:
        # Update existing
        existing.title = req.title
        existing.artist = req.artist
        existing.original_text = req.original_text
        existing.sections_json = json.dumps(req.sections)
        if req.sonnet_translations:
            existing.sonnet_translations_json = json.dumps(req.sonnet_translations)
        if req.opus_translations:
            existing.opus_translations_json = json.dumps(req.opus_translations)
        db.commit()
        return {"id": existing.id, "status": "updated"}
    else:
        # Create new
        song = ScrapedSong(
            title=req.title,
            artist=req.artist,
            url=req.url,
            original_text=req.original_text,
            sections_json=json.dumps(req.sections),
            sonnet_translations_json=json.dumps(req.sonnet_translations) if req.sonnet_translations else None,
            opus_translations_json=json.dumps(req.opus_translations) if req.opus_translations else None,
        )
        db.add(song)
        db.commit()
        db.refresh(song)
        return {"id": song.id, "status": "created"}


@router.post("/backfill-artists")
def backfill_artists(db: Session = Depends(get_db)):
    """Backfill artist data from Genius API for existing songs."""
    songs = db.query(ScrapedSong).filter(ScrapedSong.primary_artist == None).all()
    updated = 0
    errors = []

    for song in songs:
        try:
            song_id = get_song_id_from_url(song.url)
            if song_id:
                details = get_song_details(song_id)
                song.primary_artist = details.get("primary_artist")
                song.primary_artist_image = details.get("primary_artist_image")
                featured = details.get("featured_artists", [])
                song.featured_artists_json = json.dumps(featured, ensure_ascii=False) if featured else None
                updated += 1
        except Exception as e:
            errors.append({"url": song.url, "error": str(e)})

    db.commit()
    return {"updated": updated, "errors": errors}


@router.get("/list")
def list_scraped(limit: int = 50, db: Session = Depends(get_db)):
    """List all scraped songs."""
    songs = db.query(ScrapedSong).order_by(ScrapedSong.updated_at.desc()).limit(limit).all()
    return {
        "songs": [
            {
                "id": s.id,
                "title": s.title,
                "artist": s.artist,
                "url": s.url,
                "primary_artist": s.primary_artist,
                "primary_artist_image": s.primary_artist_image,
                "featured_artists": json.loads(s.featured_artists_json) if s.featured_artists_json else [],
                "has_sonnet": s.sonnet_translations_json is not None,
                "has_opus": s.opus_translations_json is not None,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in songs
        ]
    }


@router.get("/{song_id}")
def get_scraped(song_id: int, db: Session = Depends(get_db)):
    """Get a scraped song with all its data."""
    song = db.query(ScrapedSong).filter(ScrapedSong.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    return {
        "id": song.id,
        "title": song.title,
        "artist": song.artist,
        "url": song.url,
        "primary_artist": song.primary_artist,
        "primary_artist_image": song.primary_artist_image,
        "featured_artists": json.loads(song.featured_artists_json) if song.featured_artists_json else [],
        "original_text": song.original_text,
        "sections": json.loads(song.sections_json) if song.sections_json else [],
        "sonnet_translations": json.loads(song.sonnet_translations_json) if song.sonnet_translations_json else {},
        "opus_translations": json.loads(song.opus_translations_json) if song.opus_translations_json else {},
        "created_at": song.created_at.isoformat() if song.created_at else None,
        "updated_at": song.updated_at.isoformat() if song.updated_at else None,
    }


@router.patch("/{song_id}/translations")
def update_translations(song_id: int, req: UpdateTranslationsRequest, db: Session = Depends(get_db)):
    """Update translations for a scraped song."""
    song = db.query(ScrapedSong).filter(ScrapedSong.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    if req.sonnet_translations is not None:
        song.sonnet_translations_json = json.dumps(req.sonnet_translations)
    if req.opus_translations is not None:
        song.opus_translations_json = json.dumps(req.opus_translations)

    db.commit()
    return {"status": "updated"}


@router.delete("/{song_id}")
def delete_scraped(song_id: int, db: Session = Depends(get_db)):
    """Delete a scraped song."""
    song = db.query(ScrapedSong).filter(ScrapedSong.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    db.delete(song)
    db.commit()
    return {"status": "deleted"}
