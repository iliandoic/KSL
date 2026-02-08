import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.connection import Base
from database.models import StylePattern, CorpusLine
from style.analyzer import analyze_text, store_style_patterns, get_style_context
from style.importer import import_text


def get_test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


SAMPLE_TEXT = """Имам пари да хвърлям по улицата
Карам мерцедес с пълна газ
Златни вериги блестят на врата
Шампанско лея всяка нощ без спиране
Не спирам да печеля пари и пак
Животът е купон за мен тази нощ
Всички знаят моето име по клубовете
Парите идват когато работиш здраво
Никой не може да ме спре от успеха
Крал на нощта и на деня"""


def test_analyze_text():
    analysis = analyze_text(SAMPLE_TEXT)
    assert "vocabulary" in analysis
    assert "rhyme_patterns" in analysis
    assert "avg_syllables" in analysis
    assert analysis["avg_syllables"] > 0
    assert len(analysis["vocabulary"]) > 0


def test_top_vocabulary_order():
    analysis = analyze_text(SAMPLE_TEXT)
    vocab = analysis["vocabulary"]
    # "пари" appears twice, should be in vocabulary
    assert "пари" in vocab or "нощ" in vocab


def test_avg_syllable_count():
    analysis = analyze_text(SAMPLE_TEXT)
    # Should be reasonable (6-12 range for these lines)
    assert 5 <= analysis["avg_syllables"] <= 15


def test_store_style_patterns():
    db = get_test_db()
    analysis = analyze_text(SAMPLE_TEXT)
    stored = store_style_patterns(SAMPLE_TEXT, analysis, db)
    assert stored > 0
    # Verify rows in DB
    count = db.query(StylePattern).count()
    assert count > 0
    # Should have vocab_freq entries
    vocab_entries = db.query(StylePattern).filter_by(pattern_type="vocab_freq").count()
    assert vocab_entries > 0
    db.close()


def test_import_my_lyrics():
    db = get_test_db()
    result = import_text(SAMPLE_TEXT, mode="my_lyrics", db=db)
    assert result["status"] == "ok"
    assert result["details"]["patterns_stored"] > 0
    assert result["details"]["avg_syllables"] > 0
    db.close()


def test_import_reference():
    db = get_test_db()
    result = import_text(SAMPLE_TEXT, mode="reference", source="test_artist", db=db)
    assert result["status"] == "ok"
    assert result["details"]["lines_added"] > 0
    # Verify corpus_lines also populated
    corpus_count = db.query(CorpusLine).count()
    assert corpus_count > 0
    db.close()


def test_get_style_context():
    db = get_test_db()
    analysis = analyze_text(SAMPLE_TEXT)
    store_style_patterns(SAMPLE_TEXT, analysis, db)
    context = get_style_context(db)
    assert isinstance(context, str)
    assert len(context) > 0
    assert "Често използвани думи" in context
    db.close()


def test_empty_import():
    db = get_test_db()
    result = import_text("", db=db)
    assert result["status"] == "empty"
    db.close()
