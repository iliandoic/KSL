from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from library.corpus import ingest_lyrics, search_lines
from library.scraper import scrape_genius

router = APIRouter(prefix="/api/corpus", tags=["corpus"])


class IngestRequest(BaseModel):
    text: str
    source: str | None = None


class IngestUrlRequest(BaseModel):
    url: str


class SearchRequest(BaseModel):
    theme: str | None = None
    syllables: int | None = None
    rhyme_ending: str | None = None
    query: str | None = None


@router.post("/ingest")
def ingest(req: IngestRequest, db: Session = Depends(get_db)):
    result = ingest_lyrics(req.text, req.source, db)
    return result


@router.post("/ingest-url")
def ingest_url(req: IngestUrlRequest, db: Session = Depends(get_db)):
    """Scrape lyrics from a Genius URL and ingest into corpus."""
    try:
        scraped = scrape_genius(req.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to scrape: {e}")

    if not scraped["lyrics"]:
        raise HTTPException(status_code=400, detail="No lyrics found at URL")

    result = ingest_lyrics(scraped["lyrics"], scraped["artist"], db)
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
    )
    return {"lines": results}
