"""
Reference corpus management. Users paste lyrics from artists they like.
The app processes them into a searchable, AI-powering reference corpus.

Key design note: pasted lyrics are often NOT Bulgarian (Bosnian, Serbian,
Romanian, French, English). The system handles them gracefully.
"""
import re

from sqlalchemy.orm import Session
from sqlalchemy import func

from database.models import CorpusLine, RhymeableWord, ImportedSong
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
        if db.query(RhymeableWord).filter_by(word=word).first():
            continue
        rhyme_group = compute_rhyme_group(word)
        syllables = count_word_syllables(word)
        theme = detect_theme(word)
        db.add(RhymeableWord(
            word=word,
            rhyme_group=rhyme_group,
            syllable_count=syllables,
            theme=theme,
            phonetic_ending=rhyme_group,
            source=source,
        ))
        added += 1
    return added


def ingest_lyrics(
    text: str,
    source: str | None,
    db: Session,
    sections: list | None = None,
    title: str | None = None,
    url: str | None = None,
) -> dict:
    """
    Ingest pasted lyrics text. Splits into individual lines,
    auto-tags each with syllable count, phonetic ending, theme, and section.

    If sections is provided (from scraper), uses that for section tagging.
    Otherwise, parses section headers from the text itself.

    Returns: {"lines_added": int, "themes_detected": {theme: count}, "sections_found": {section: count}}
    """
    if not text or not text.strip():
        return {"lines_added": 0, "themes_detected": {}, "words_added": 0, "sections_found": {}, "song_id": None}

    themes_detected = {}
    sections_found = {}
    added = 0
    song_id = None

    # Create ImportedSong record if we have song metadata
    if title or url:
        song = ImportedSong(
            title=title,
            artist=source,
            url=url,
        )
        db.add(song)
        db.flush()  # Get the ID
        song_id = song.id

    if sections:
        # Use structured sections from scraper
        for section_data in sections:
            section_type = section_data.get("section", "verse")
            for line_text in section_data.get("lines", []):
                added += _ingest_line(line_text, source, section_type, db, themes_detected, song_id)
                sections_found[section_type] = sections_found.get(section_type, 0) + 1
    else:
        # Parse sections from text (for manual paste)
        current_section = None
        for line in text.strip().split("\n"):
            line_text = line.strip()
            if not line_text:
                continue

            # Check for section header
            if re.match(r"^\[.*\]$", line_text):
                current_section = _parse_section_header(line_text)
                continue

            section_type = current_section or "verse"
            added += _ingest_line(line_text, source, section_type, db, themes_detected, song_id)
            sections_found[section_type] = sections_found.get(section_type, 0) + 1

    # Update song stats if we created one
    if song_id:
        song.hook_count = sections_found.get("hook", 0)
        song.verse_count = sections_found.get("verse", 0)
        song.has_intro = 1 if "intro" in sections_found else 0
        song.has_outro = 1 if "outro" in sections_found else 0
        song.has_bridge = 1 if "bridge" in sections_found else 0
        song.total_lines = added

    # Extract individual Cyrillic words into the rhymes table
    words_added = _extract_words_to_rhymes(text, source, db)

    db.commit()
    return {
        "lines_added": added,
        "themes_detected": themes_detected,
        "words_added": words_added,
        "sections_found": sections_found,
        "song_id": song_id,
    }


def _parse_section_header(header: str) -> str | None:
    """Parse section header like [Refren] to normalized type."""
    clean = header.strip("[]").lower()
    clean = re.sub(r"\s*\d+\s*", "", clean)  # Remove numbers
    clean = re.sub(r"\s*\(.*?\)\s*", "", clean)  # Remove (x2) etc
    clean = clean.strip()

    section_map = {
        "refren": "hook", "chorus": "hook", "hook": "hook", "припев": "hook",
        "pre-refren": "pre-hook", "pre-chorus": "pre-hook", "prechorus": "pre-hook",
        "verse": "verse", "strofa": "verse", "vers": "verse", "куплет": "verse",
        "bridge": "bridge", "pod": "bridge", "мост": "bridge",
        "intro": "intro", "outro": "outro",
        "post-chorus": "post-hook", "post-refren": "post-hook",
    }

    if clean in section_map:
        return section_map[clean]
    for key, val in section_map.items():
        if clean.startswith(key):
            return val
    return None


def _ingest_line(
    line_text: str,
    source: str | None,
    section: str | None,
    db: Session,
    themes_detected: dict,
    song_id: int | None = None,
) -> int:
    """Ingest a single line into the corpus. Returns 1 if added, 0 otherwise."""
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
        song_id=song_id,
        language=language,
        theme=theme,
        section=section,
        syllables=syllables,
        phonetic_ending=phonetic_ending,
    )
    db.add(corpus_line)

    if theme:
        themes_detected[theme] = themes_detected.get(theme, 0) + 1

    return 1


def search_lines(
    db: Session,
    theme: str | None = None,
    syllable_count: int | None = None,
    rhyme_ending: str | None = None,
    query: str | None = None,
    section: str | None = None,
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
    if section:
        q = q.filter(CorpusLine.section == section)

    results = q.limit(50).all()
    return [
        {
            "id": r.id,
            "line": r.line,
            "source": r.source,
            "song_id": r.song_id,
            "language": r.language,
            "theme": r.theme,
            "section": r.section,
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


def get_corpus_stats(db: Session) -> dict:
    """Get aggregate stats about the corpus."""
    total_lines = db.query(func.count(CorpusLine.id)).scalar() or 0
    total_songs = db.query(func.count(ImportedSong.id)).scalar() or 0

    # Section breakdown
    section_counts = (
        db.query(CorpusLine.section, func.count(CorpusLine.id))
        .group_by(CorpusLine.section)
        .all()
    )

    # Song structure stats
    songs_with_hooks = db.query(func.count(ImportedSong.id)).filter(ImportedSong.hook_count > 0).scalar() or 0
    songs_with_intro = db.query(func.count(ImportedSong.id)).filter(ImportedSong.has_intro == 1).scalar() or 0
    songs_with_outro = db.query(func.count(ImportedSong.id)).filter(ImportedSong.has_outro == 1).scalar() or 0
    songs_with_bridge = db.query(func.count(ImportedSong.id)).filter(ImportedSong.has_bridge == 1).scalar() or 0

    return {
        "total_lines": total_lines,
        "total_songs": total_songs,
        "sections": {s: c for s, c in section_counts if s},
        "songs_with_hooks": songs_with_hooks,
        "songs_with_intro": songs_with_intro,
        "songs_with_outro": songs_with_outro,
        "songs_with_bridge": songs_with_bridge,
    }


def get_imported_songs(db: Session, limit: int = 50) -> list[dict]:
    """Get list of imported songs with their structure info."""
    songs = db.query(ImportedSong).order_by(ImportedSong.created_at.desc()).limit(limit).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "artist": s.artist,
            "url": s.url,
            "hook_count": s.hook_count,
            "verse_count": s.verse_count,
            "has_intro": bool(s.has_intro),
            "has_outro": bool(s.has_outro),
            "has_bridge": bool(s.has_bridge),
            "total_lines": s.total_lines,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in songs
    ]
