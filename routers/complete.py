from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from engines.ai import complete_lines
from engines.syllable import count_syllables
from library.corpus import get_context_lines
from style.analyzer import get_style_context

router = APIRouter(prefix="/api", tags=["complete"])


class CompleteRequest(BaseModel):
    lines: list[str]
    theme: str | None = None
    count: int = 3


@router.post("/complete")
def complete(req: CompleteRequest, db: Session = Depends(get_db)):
    # Build context
    style_ctx = get_style_context(db)
    corpus_ctx = ""
    if req.theme:
        corpus_lines = get_context_lines(req.theme, 5, db)
        corpus_ctx = "\n".join(corpus_lines)

    # Calculate target syllable count from existing lines
    syllable_target = None
    if req.lines:
        counts = [count_syllables(line) for line in req.lines]
        syllable_target = round(sum(counts) / len(counts))

    suggestions = complete_lines(
        lines=req.lines,
        theme=req.theme,
        style_context=style_ctx,
        corpus_context=corpus_ctx,
        count=req.count,
        syllable_target=syllable_target,
    )

    return {
        "suggestions": suggestions,
        "syllable_target": syllable_target,
    }
