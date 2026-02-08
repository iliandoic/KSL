from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from library.corpus import ingest_lyrics, search_lines, get_corpus_stats, get_imported_songs
from library.scraper import scrape_genius

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
