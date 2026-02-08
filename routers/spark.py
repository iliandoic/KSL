from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from engines.spark import generate_titles, generate_opening_lines, random_spark, word_explosion

router = APIRouter(prefix="/api/spark", tags=["spark"])


class TitlesRequest(BaseModel):
    theme: str | None = None


class FromTitleRequest(BaseModel):
    title: str


class ExplodeRequest(BaseModel):
    word: str


@router.post("/titles")
def spark_titles(req: TitlesRequest):
    titles = generate_titles(theme=req.theme)
    return {"titles": titles}


@router.post("/from-title")
def spark_from_title(req: FromTitleRequest):
    lines = generate_opening_lines(req.title)
    return {"opening_lines": lines}


@router.post("/random")
def spark_random():
    result = random_spark()
    return result


@router.post("/explode")
def spark_explode(req: ExplodeRequest, db: Session = Depends(get_db)):
    result = word_explosion(req.word, db)
    return result
