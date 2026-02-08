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


class CorpusLine(Base):
    __tablename__ = "corpus_lines"

    id = Column(Integer, primary_key=True)
    line = Column(Text, nullable=False)
    source = Column(String(200))
    language = Column(String(20), default="bg")
    theme = Column(String(50))
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
