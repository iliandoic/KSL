"""
Freestyle router - aggregated endpoints for instant inspiration.
Pulls from all studied artists to provide random sparks.
"""
import json
import random

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import ArtistStudy, ArtistRhymeGroup

router = APIRouter(prefix="/api/freestyle", tags=["freestyle"])


@router.get("/spark")
def random_spark(db: Session = Depends(get_db)):
    """
    Get a random inspiration from any category.
    Cycles through: concept, prompt, title, ending, word.
    """
    spark_types = ["concept", "prompt", "title", "ending", "word"]
    spark_type = random.choice(spark_types)

    if spark_type == "concept":
        concepts = _get_all_concepts(db)
        if concepts:
            return {"type": "concept", "value": random.choice(concepts)}

    elif spark_type == "prompt":
        prompts = _get_all_prompts(db)
        if prompts:
            return {"type": "prompt", "value": random.choice(prompts)}

    elif spark_type == "title":
        titles = _get_all_titles(db)
        if titles:
            return {"type": "title", "value": random.choice(titles)}

    elif spark_type == "ending":
        endings = _get_all_endings(db)
        if endings:
            ending = random.choice(endings)
            return {"type": "ending", "value": ending["ending"], "group": ending["group"]}

    elif spark_type == "word":
        words = _get_top_vocabulary(db, limit=100)
        if words:
            word = random.choice(words)
            return {"type": "word", "value": word["word"]}

    # Fallback if no data
    return {"type": "empty", "value": "Study some artists first!"}


@router.get("/concepts")
def get_concepts(db: Session = Depends(get_db)):
    """Get all concepts from all artists."""
    concepts = _get_all_concepts(db)
    return {"concepts": concepts}


@router.get("/prompts")
def get_prompts(db: Session = Depends(get_db)):
    """Get all prompts from all artists."""
    prompts = _get_all_prompts(db)
    return {"prompts": prompts}


@router.get("/titles")
def get_titles(db: Session = Depends(get_db)):
    """Get all titles from all artists."""
    titles = _get_all_titles(db)
    return {"titles": titles}


@router.get("/vocabulary")
def get_vocabulary(limit: int = 50, db: Session = Depends(get_db)):
    """Get top vocabulary words across all artists."""
    words = _get_top_vocabulary(db, limit=limit)
    return {"words": words}


@router.get("/endings")
def get_endings(db: Session = Depends(get_db)):
    """Get all rhyme endings grouped by sound."""
    groups = _get_all_ending_groups(db)
    return {"groups": groups}


# Helper functions

def _get_all_concepts(db: Session) -> list[str]:
    """Aggregate all concepts from all artists."""
    studies = db.query(ArtistStudy).all()
    concepts = []
    for s in studies:
        if s.concepts_json:
            concepts.extend(json.loads(s.concepts_json))
    return list(set(concepts))  # Dedupe


def _get_all_prompts(db: Session) -> list[str]:
    """Aggregate all prompts from all artists."""
    studies = db.query(ArtistStudy).all()
    prompts = []
    for s in studies:
        if s.prompts_json:
            prompts.extend(json.loads(s.prompts_json))
    return list(set(prompts))


def _get_all_titles(db: Session) -> list[str]:
    """Aggregate all titles from all artists."""
    studies = db.query(ArtistStudy).all()
    titles = []
    for s in studies:
        if s.titles_json:
            titles.extend(json.loads(s.titles_json))
    return list(set(titles))


def _get_top_vocabulary(db: Session, limit: int = 50) -> list[dict]:
    """Get top vocabulary words across all artists by frequency."""
    studies = db.query(ArtistStudy).all()
    combined = {}
    for s in studies:
        if s.vocabulary_json:
            vocab = json.loads(s.vocabulary_json)
            for word, count in vocab.items():
                combined[word] = combined.get(word, 0) + count

    # Sort by frequency
    sorted_words = sorted(combined.items(), key=lambda x: x[1], reverse=True)
    return [{"word": w, "count": c} for w, c in sorted_words[:limit]]


def _get_all_endings(db: Session) -> list[dict]:
    """Get all unique endings as flat list."""
    groups = db.query(ArtistRhymeGroup).all()
    endings = []
    for g in groups:
        if g.endings_json:
            for ending in json.loads(g.endings_json):
                endings.append({"ending": ending, "group": g.group_name})
    return endings


def _get_all_ending_groups(db: Session) -> list[dict]:
    """Get all rhyme groups aggregated across artists."""
    groups = db.query(ArtistRhymeGroup).all()

    # Aggregate by group name
    aggregated = {}
    for g in groups:
        if g.group_name not in aggregated:
            aggregated[g.group_name] = {
                "group_name": g.group_name,
                "endings": [],
                "frequency": 0,
            }
        if g.endings_json:
            endings = json.loads(g.endings_json)
            for e in endings:
                if e not in aggregated[g.group_name]["endings"]:
                    aggregated[g.group_name]["endings"].append(e)
        aggregated[g.group_name]["frequency"] += g.frequency or 0

    # Sort by frequency
    result = sorted(aggregated.values(), key=lambda x: x["frequency"], reverse=True)
    return result
