"""
Style importer - handles text import for style learning and reference corpus.
Two modes: "my_lyrics" (for style learning) vs "reference" (feeds the corpus).
"""
from sqlalchemy.orm import Session

from style.analyzer import analyze_text, store_style_patterns
from library.corpus import ingest_lyrics


def import_text(
    text: str,
    mode: str = "my_lyrics",
    source: str | None = None,
    db: Session = None,
    user_id: str = "default",
) -> dict:
    """
    Import lyrics text.

    mode="my_lyrics": Analyze for style patterns (user's own writing)
    mode="reference": Ingest into corpus for search + AI context

    Returns import result with details.
    """
    if not text or not text.strip():
        return {"status": "empty", "details": {}}

    result = {"status": "ok", "mode": mode, "details": {}}

    if mode == "my_lyrics":
        # Analyze for style patterns
        analysis = analyze_text(text)
        stored = store_style_patterns(text, analysis, db, user_id)
        result["details"] = {
            "patterns_stored": stored,
            "avg_syllables": analysis["avg_syllables"],
            "top_vocabulary": list(analysis["vocabulary"].keys())[:10],
            "rhyme_patterns_found": len(analysis["rhyme_patterns"]),
        }
    elif mode == "reference":
        # Ingest into corpus AND analyze for patterns
        corpus_result = ingest_lyrics(text, source, db)
        analysis = analyze_text(text)
        store_style_patterns(text, analysis, db, user_id)
        result["details"] = {
            "lines_added": corpus_result["lines_added"],
            "themes_detected": corpus_result["themes_detected"],
            "avg_syllables": analysis["avg_syllables"],
        }

    return result
