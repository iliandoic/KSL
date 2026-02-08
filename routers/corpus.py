import json
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import ScrapedSong
from library.corpus import ingest_lyrics, search_lines, get_corpus_stats, get_imported_songs
from library.scraper import scrape_genius
from library.genius_api import get_song_id_from_url, get_song_details
from library.study import study_song
from engines.ai import translate_lines

router = APIRouter(prefix="/api/corpus", tags=["corpus"])


class IngestRequest(BaseModel):
    text: str
    source: str | None = None
    sections: list | None = None
    title: str | None = None
    url: str | None = None


class IngestUrlRequest(BaseModel):
    url: str


class SearchRequest(BaseModel):
    theme: str | None = None
    syllables: int | None = None
    rhyme_ending: str | None = None
    query: str | None = None
    section: str | None = None  # hook, verse, pre-hook, bridge, intro, outro


@router.post("/ingest")
def ingest(req: IngestRequest, db: Session = Depends(get_db)):
    result = ingest_lyrics(
        req.text,
        req.source,
        db,
        sections=req.sections,
        title=req.title,
        url=req.url,
    )
    return result


@router.post("/scrape-url")
def scrape_url(req: IngestUrlRequest):
    """Scrape lyrics from a Genius URL without ingesting."""
    try:
        scraped = scrape_genius(req.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to scrape: {e}")

    if not scraped["lyrics"]:
        raise HTTPException(status_code=400, detail="No lyrics found at URL")

    return {
        "title": scraped["title"],
        "artist": scraped["artist"],
        "lyrics": scraped["lyrics"],
        "sections": scraped["sections"],
        "url": req.url,
    }


@router.post("/ingest-url")
def ingest_url(req: IngestUrlRequest, db: Session = Depends(get_db)):
    """Scrape lyrics from a Genius URL and ingest into corpus."""
    try:
        scraped = scrape_genius(req.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to scrape: {e}")

    if not scraped["lyrics"]:
        raise HTTPException(status_code=400, detail="No lyrics found at URL")

    result = ingest_lyrics(
        scraped["lyrics"],
        scraped["artist"],
        db,
        sections=scraped["sections"],
        title=scraped["title"],
        url=req.url,
    )
    return {
        "title": scraped["title"],
        "artist": scraped["artist"],
        **result,
    }


@router.post("/search")
def search(req: SearchRequest, db: Session = Depends(get_db)):
    results = search_lines(
        db=db,
        theme=req.theme,
        syllable_count=req.syllables,
        rhyme_ending=req.rhyme_ending,
        query=req.query,
        section=req.section,
    )
    return {"lines": results}


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    """Get corpus statistics including section breakdowns."""
    return get_corpus_stats(db)


@router.get("/songs")
def songs(limit: int = 50, db: Session = Depends(get_db)):
    """Get list of imported songs with their structure info."""
    return {"songs": get_imported_songs(db, limit)}


class TranslateRequest(BaseModel):
    lines: list[str]
    target_lang: str = "en"  # "en" or "bg"
    model: str = "sonnet"  # "sonnet" or "opus"


@router.post("/translate")
def translate(req: TranslateRequest):
    """Translate lines to target language using Claude."""
    if not req.lines:
        return {"translations": []}

    try:
        translations = translate_lines(req.lines, req.target_lang, req.model)
        return {"translations": translations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {e}")


class ScrapeAndStudyRequest(BaseModel):
    url: str
    model: str = "sonnet"  # Translation model


def _detect_language(text: str) -> str:
    """Detect if text is primarily Cyrillic (Bulgarian) or Latin."""
    cyrillic = len(re.findall(r'[\u0400-\u04FF]', text))
    latin = len(re.findall(r'[a-zA-Z]', text))
    return "bg" if cyrillic > latin else "other"


def _extract_all_lines(sections: list) -> list[str]:
    """Extract all lines from sections structure."""
    lines = []
    for section in sections:
        lines.extend(section.get("lines", []))
    return lines


@router.post("/scrape-and-study")
def scrape_and_study(req: ScrapeAndStudyRequest, db: Session = Depends(get_db)):
    """
    Atomic operation: Scrape + Translate + Save + Study.
    This is the main entry point for adding songs to the inspiration pool.
    """
    # 1. Scrape lyrics
    try:
        scraped = scrape_genius(req.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to scrape: {e}")

    if not scraped["lyrics"]:
        raise HTTPException(status_code=400, detail="No lyrics found at URL")

    title = scraped["title"]
    artist = scraped["artist"]
    original_text = scraped["lyrics"]
    sections = scraped["sections"]

    # 1b. Get structured artist data from Genius API
    primary_artist = None
    primary_artist_image = None
    featured_artists = []

    song_id = get_song_id_from_url(req.url)
    if song_id:
        try:
            details = get_song_details(song_id)
            primary_artist = details.get("primary_artist")
            primary_artist_image = details.get("primary_artist_image")
            featured_artists = details.get("featured_artists", [])
        except Exception:
            pass  # Fall back to scraped artist string

    # 2. Detect language and translate if needed
    language = _detect_language(original_text)
    translations = {}

    if language == "bg":
        # Bulgarian - use original as translation
        all_lines = _extract_all_lines(sections)
        for i, line in enumerate(all_lines):
            translations[f"line_{i}"] = line
    else:
        # Foreign - translate to Bulgarian
        all_lines = _extract_all_lines(sections)
        if all_lines:
            try:
                translated = translate_lines(all_lines, "bg", req.model)
                for i, line in enumerate(translated):
                    translations[f"line_{i}"] = line
            except Exception as e:
                # Continue without translation on error
                pass

    # 3. Save to ScrapedSong (upsert by URL)
    existing = db.query(ScrapedSong).filter_by(url=req.url).first()
    if existing:
        song = existing
        song.title = title
        song.artist = artist
        song.original_text = original_text
        song.sections_json = json.dumps(sections, ensure_ascii=False)
        song.primary_artist = primary_artist
        song.primary_artist_image = primary_artist_image
        song.featured_artists_json = json.dumps(featured_artists, ensure_ascii=False) if featured_artists else None
        if req.model == "sonnet":
            song.sonnet_translations_json = json.dumps(translations, ensure_ascii=False)
        else:
            song.opus_translations_json = json.dumps(translations, ensure_ascii=False)
    else:
        song = ScrapedSong(
            title=title,
            artist=artist,
            url=req.url,
            original_text=original_text,
            sections_json=json.dumps(sections, ensure_ascii=False),
            primary_artist=primary_artist,
            primary_artist_image=primary_artist_image,
            featured_artists_json=json.dumps(featured_artists, ensure_ascii=False) if featured_artists else None,
        )
        if req.model == "sonnet":
            song.sonnet_translations_json = json.dumps(translations, ensure_ascii=False)
        else:
            song.opus_translations_json = json.dumps(translations, ensure_ascii=False)
        db.add(song)

    db.commit()
    db.refresh(song)

    # 4. Study the artist
    study_result = study_song(song, db)

    return {
        "song_id": song.id,
        "title": title,
        "artist": artist,
        "language": language,
        "lines_translated": len(translations),
        "study": study_result,
    }
