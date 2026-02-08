from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from engines.rhyme import find_rhymes, extract_phonetic_ending
from engines.syllable import count_syllables, syllable_breakdown

router = APIRouter(prefix="/api", tags=["rhymes"])


class RhymeRequest(BaseModel):
    word: str


class SyllableRequest(BaseModel):
    line: str


@router.post("/rhymes")
def get_rhymes(req: RhymeRequest, db: Session = Depends(get_db)):
    result = find_rhymes(req.word, db)
    phonetic = extract_phonetic_ending(req.word)
    return {
        "word": req.word,
        "phonetic_ending": phonetic,
        **result,
    }


@router.post("/syllables")
def get_syllables(req: SyllableRequest):
    breakdown = syllable_breakdown(req.line)
    return {
        "line": req.line,
        "count": breakdown["total"],
        "words": breakdown["words"],
    }
