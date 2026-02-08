"""
Reference corpus management. Users paste lyrics from artists they like.
The app processes them into a searchable, AI-powering reference corpus.

Key design note: pasted lyrics are often NOT Bulgarian (Bosnian, Serbian,
Romanian, French, English). The system handles them gracefully.
"""
import re

from sqlalchemy.orm import Session

from database.models import CorpusLine, Rhyme
from engines.syllable import count_syllables, count_word_syllables
from engines.rhyme import compute_rhyme_group
from library.themes import detect_theme

# Minimum word length to be worth adding to rhyme DB
MIN_WORD_LENGTH = 3


def _detect_language(line: str) -> str:
    """Simple language detection based on character sets."""
    cyrillic_count = sum(1 for c in line if "\u0400" <= c <= "\u04FF")
    latin_count = sum(1 for c in line if "a" <= c.lower() <= "z" or "\u00C0" <= c <= "\u024F")

    if cyrillic_count > latin_count:
        return "bg"  # Could be Bulgarian, Serbian, Bosnian - all use Cyrillic
    elif latin_count > 0:
        return "other"  # Romanian, French, English, Latin-script Serbian/Bosnian
    return "unknown"


def _extract_words_to_rhymes(text: str, source: str | None, db: Session) -> int:
    """
    Extract individual Cyrillic words from text and add new ones to the rhymes table.
    Only adds words that are Cyrillic, >= MIN_WORD_LENGTH chars, and not already in DB.
    Stores the source (artist/song) so we know where each word came from.
    Returns count of new words added.
    """
    # Extract all Cyrillic words
    raw_words = re.findall(r"[а-яёА-ЯЁ]+", text.lower())
    # Deduplicate and filter
    unique_words = set(w for w in raw_words if len(w) >= MIN_WORD_LENGTH)

    added = 0
    for word in unique_words:
        # Skip if already in DB
        if db.query(Rhyme).filter_by(word=word).first():
            continue
        rhyme_group = compute_rhyme_group(word)
        syllables = count_word_syllables(word)
        theme = detect_theme(word)
        db.add(Rhyme(
            word=word,
            rhyme_group=rhyme_group,
            syllable_count=syllables,
            theme=theme,
            phonetic_ending=rhyme_group,
            source=source,
        ))
        added += 1
    return added


def ingest_lyrics(text: str, source: str | None, db: Session) -> dict:
    """
    Ingest pasted lyrics text. Splits into individual lines,
    auto-tags each with syllable count, phonetic ending, and theme.

    Returns: {"lines_added": int, "themes_detected": {theme: count}}
    """
    if not text or not text.strip():
        return {"lines_added": 0, "themes_detected": {}}

    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    themes_detected = {}
    added = 0

    for line_text in lines:
        language = _detect_language(line_text)
        theme = detect_theme(line_text)
        syllables = count_syllables(line_text)

        # Only compute Bulgarian phonetic ending for Cyrillic text
        phonetic_ending = ""
        if language == "bg":
            words = line_text.strip().split()
            if words:
                last_word = words[-1]
                phonetic_ending = compute_rhyme_group(last_word)

        corpus_line = CorpusLine(
            line=line_text,
            source=source,
            language=language,
            theme=theme,
            syllables=syllables,
            phonetic_ending=phonetic_ending,
        )
        db.add(corpus_line)
        added += 1

        if theme:
            themes_detected[theme] = themes_detected.get(theme, 0) + 1

    # Extract individual Cyrillic words into the rhymes table
    words_added = _extract_words_to_rhymes(text, source, db)

    db.commit()
    return {"lines_added": added, "themes_detected": themes_detected, "words_added": words_added}


def search_lines(
    db: Session,
    theme: str | None = None,
    syllable_count: int | None = None,
    rhyme_ending: str | None = None,
    query: str | None = None,
) -> list[dict]:
    """Search the corpus with optional filters."""
    q = db.query(CorpusLine)

    if theme:
        q = q.filter(CorpusLine.theme == theme)
    if syllable_count is not None:
        q = q.filter(CorpusLine.syllables == syllable_count)
    if rhyme_ending:
        q = q.filter(CorpusLine.phonetic_ending == rhyme_ending)
    if query:
        q = q.filter(CorpusLine.line.ilike(f"%{query}%"))

    results = q.limit(50).all()
    return [
        {
            "id": r.id,
            "line": r.line,
            "source": r.source,
            "language": r.language,
            "theme": r.theme,
            "syllables": r.syllables,
            "phonetic_ending": r.phonetic_ending,
        }
        for r in results
    ]


def get_context_lines(theme: str, count: int, db: Session) -> list[str]:
    """Pull relevant lines to inject into Claude prompts as few-shot examples."""
    results = (
        db.query(CorpusLine)
        .filter(CorpusLine.theme == theme)
        .limit(count)
        .all()
    )
    return [r.line for r in results]
