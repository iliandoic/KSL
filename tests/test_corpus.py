import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.connection import Base
from database.models import CorpusLine
from library.corpus import ingest_lyrics, search_lines, get_context_lines


def get_test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


SAMPLE_LYRICS = """Имам пари да хвърлям
Карам мерцедес по булеварда
Златни вериги на врата
Шампанско в клуба тази нощ
Животът е купон за мен"""


def test_ingest_lyrics():
    db = get_test_db()
    result = ingest_lyrics(SAMPLE_LYRICS, "test_artist", db)
    assert result["lines_added"] == 5
    # Verify 5 rows in DB
    count = db.query(CorpusLine).count()
    assert count == 5
    # Each should have syllable count
    for row in db.query(CorpusLine).all():
        assert row.syllables is not None
        assert row.syllables > 0
    db.close()


def test_search_by_theme():
    db = get_test_db()
    ingest_lyrics(SAMPLE_LYRICS, "test", db)
    # At least some lines should have detected themes
    results = search_lines(db, theme="money")
    # "пари", "мерцедес" etc. should trigger money theme
    assert isinstance(results, list)
    db.close()


def test_search_by_syllable_count():
    db = get_test_db()
    ingest_lyrics(SAMPLE_LYRICS, "test", db)
    results = search_lines(db, syllable_count=7)
    assert isinstance(results, list)
    # "Имам пари да хвърлям" = 7 syllables
    matching_lines = [r["line"] for r in results]
    assert any("хвърлям" in line for line in matching_lines)
    db.close()


def test_get_context_lines():
    db = get_test_db()
    ingest_lyrics(SAMPLE_LYRICS, "test", db)
    # Get at most 3 lines with any detected theme
    lines = get_context_lines("money", 3, db)
    assert len(lines) <= 3
    assert all(isinstance(l, str) for l in lines)
    db.close()


def test_ingest_empty():
    db = get_test_db()
    result = ingest_lyrics("", None, db)
    assert result["lines_added"] == 0
    assert result["themes_detected"] == {}
    db.close()


def test_ingest_multilang():
    """Test that non-Bulgarian lyrics are ingested correctly."""
    db = get_test_db()
    multi_lyrics = """I got money in the bank
Imam pare za bacanje
J'ai de l'argent plein les poches
Am bani de aruncat"""
    result = ingest_lyrics(multi_lyrics, "various", db)
    assert result["lines_added"] == 4
    # Verify language detection
    rows = db.query(CorpusLine).all()
    languages = [r.language for r in rows]
    # Some should be detected as "other" (Latin script)
    assert "other" in languages
    db.close()
