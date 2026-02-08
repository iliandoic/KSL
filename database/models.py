from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Index

from database.connection import Base


class RhymeableWord(Base):
    """Bulgarian words extracted from lyrics, with phonetic data for rhyme matching."""
    __tablename__ = "rhymeable_words"

    id = Column(Integer, primary_key=True)
    word = Column(String(100), nullable=False, unique=True)
    phonetic_ending = Column(String(50))
    rhyme_group = Column(String(50), index=True)
    syllable_count = Column(Integer)
    theme = Column(String(50))
    source = Column(String(200))  # artist/song where this word was first seen
    created_at = Column(DateTime, default=datetime.utcnow)


class ArtistStudy(Base):
    """Aggregated study data for an artist across all their songs."""
    __tablename__ = "artist_studies"

    id = Column(Integer, primary_key=True)
    artist = Column(String(200), unique=True, index=True)
    songs_studied = Column(Integer, default=0)
    vocabulary_json = Column(Text)  # JSON: {"пари": 15, "любов": 12, ...}
    concepts_json = Column(Text)  # JSON: ["proving haters wrong", "self-made success", ...]
    prompts_json = Column(Text)  # JSON: ["Who doubted you?", "What's your comeback?", ...]
    titles_json = Column(Text)  # JSON: ["Money Talks", "Trust Nobody", ...]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ArtistRhymeGroup(Base):
    """Rhyme endings grouped by sound for an artist."""
    __tablename__ = "artist_rhyme_groups"

    id = Column(Integer, primary_key=True)
    artist = Column(String(200), index=True)
    group_name = Column(String(50))  # AI-assigned: "EE", "OT", "ATE"
    endings_json = Column(Text)  # JSON: ["-eri", "-elly", "-eady"] - original spellings kept
    example_words_json = Column(Text)  # JSON: {"-eri": ["feri", "peri"], "-elly": ["belly"]}
    frequency = Column(Integer, default=0)  # total occurrences
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


class ScrapedSong(Base):
    """Store scraped songs with translations for iteration."""
    __tablename__ = "scraped_songs"

    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    artist = Column(String(200))  # Legacy combined artist string
    url = Column(String(500))
    original_text = Column(Text)  # Raw scraped lyrics
    sections_json = Column(Text)  # JSON: [{section: str, lines: [str]}]
    sonnet_translations_json = Column(Text)  # JSON: {lineKey: translation}
    opus_translations_json = Column(Text)  # JSON: {lineKey: translation}
    # Structured artist data from Genius API
    primary_artist = Column(String(200))
    primary_artist_image = Column(String(500))
    featured_artists_json = Column(Text)  # JSON: [{"name": "...", "image": "..."}]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
