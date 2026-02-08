from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Index

from database.connection import Base


class Rhyme(Base):
    __tablename__ = "rhymes"

    id = Column(Integer, primary_key=True)
    word = Column(String(100), nullable=False, unique=True)
    phonetic_ending = Column(String(50))
    rhyme_group = Column(String(50), index=True)
    syllable_count = Column(Integer)
    theme = Column(String(50))
    source = Column(String(200))  # artist/song where this word was first seen
    created_at = Column(DateTime, default=datetime.utcnow)


class ImportedSong(Base):
    """Track imported songs for structure analysis."""
    __tablename__ = "imported_songs"

    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    artist = Column(String(200))
    url = Column(String(500))
    # Section counts for quick queries
    hook_count = Column(Integer, default=0)
    verse_count = Column(Integer, default=0)
    has_intro = Column(Integer, default=0)  # 0 or 1
    has_outro = Column(Integer, default=0)
    has_bridge = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class CorpusLine(Base):
    __tablename__ = "corpus_lines"

    id = Column(Integer, primary_key=True)
    line = Column(Text, nullable=False)
    source = Column(String(200))
    song_id = Column(Integer, index=True)  # FK to imported_songs
    language = Column(String(20), default="bg")
    theme = Column(String(50))
    section = Column(String(50))  # hook, verse, pre-hook, bridge, intro, outro
    syllables = Column(Integer)
    phonetic_ending = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class UserLyric(Base):
    __tablename__ = "user_lyrics"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), default="default")
    title = Column(String(200))
    content = Column(Text, nullable=False)
    theme = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StylePattern(Base):
    __tablename__ = "style_patterns"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), default="default")
    pattern_type = Column(String(50), nullable=False)  # vocab_freq, rhyme_pattern, avg_syllables
    key = Column(String(200), nullable=False)
    value = Column(Float)
    source_text_hash = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)


class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), default="default")
    title = Column(String(200))
    lines = Column(Text)  # JSON array of lines
    theme = Column(String(50))
    status = Column(String(20), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
