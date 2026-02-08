import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.connection import Base
from database.models import Rhyme, CorpusLine, UserLyric, StylePattern, Song


def get_test_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_create_tables():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    table_names = list(Base.metadata.tables.keys())
    assert "rhymes" in table_names
    assert "corpus_lines" in table_names
    assert "user_lyrics" in table_names
    assert "style_patterns" in table_names
    assert "songs" in table_names


def test_rhyme_model():
    db = get_test_session()
    r = Rhyme(word="любов", phonetic_ending="оф", rhyme_group="O:ф", syllable_count=2, theme="love")
    db.add(r)
    db.commit()
    result = db.query(Rhyme).filter_by(word="любов").first()
    assert result is not None
    assert result.rhyme_group == "O:ф"
    assert result.syllable_count == 2
    db.close()


def test_corpus_line_model():
    db = get_test_session()
    cl = CorpusLine(line="Имам пари да хвърлям", source="test", language="bg", theme="money", syllables=7)
    db.add(cl)
    db.commit()
    result = db.query(CorpusLine).first()
    assert result.line == "Имам пари да хвърлям"
    assert result.language == "bg"
    assert result.syllables == 7
    db.close()


def test_user_lyric_model():
    db = get_test_session()
    ul = UserLyric(content="Test lyric content", title="Test Song")
    db.add(ul)
    db.commit()
    result = db.query(UserLyric).first()
    assert result.title == "Test Song"
    assert result.user_id == "default"
    db.close()


def test_style_pattern_model():
    db = get_test_session()
    sp = StylePattern(pattern_type="vocab_freq", key="пари", value=15.0)
    db.add(sp)
    db.commit()
    result = db.query(StylePattern).first()
    assert result.pattern_type == "vocab_freq"
    assert result.value == 15.0
    db.close()


def test_song_model():
    db = get_test_session()
    s = Song(title="Нова песен", lines='["line1", "line2"]', theme="party")
    db.add(s)
    db.commit()
    result = db.query(Song).first()
    assert result.title == "Нова песен"
    assert result.status == "draft"
    db.close()
