from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from style.importer import import_text
from style.analyzer import get_style_context
from engines.ai import complete_lines

router = APIRouter(prefix="/api/style", tags=["style"])


class ImportRequest(BaseModel):
    text: str
    mode: str = "my_lyrics"  # "my_lyrics" or "reference"
    source: str | None = None


class SuggestRequest(BaseModel):
    lines: list[str]
    theme: str | None = None
    count: int = 3


@router.post("/import")
def style_import(req: ImportRequest, db: Session = Depends(get_db)):
    result = import_text(
        text=req.text,
        mode=req.mode,
        source=req.source,
        db=db,
    )
    return result


@router.post("/suggest")
def style_suggest(req: SuggestRequest, db: Session = Depends(get_db)):
    style_ctx = get_style_context(db)
    suggestions = complete_lines(
        lines=req.lines,
        theme=req.theme,
        style_context=style_ctx,
        count=req.count,
    )
    return {"suggestions": suggestions, "style_applied": bool(style_ctx)}
