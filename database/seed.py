"""
Idempotent seed runner. Run: python -m database.seed
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.connection import Base, engine
from database.models import Rhyme
from database.seed_rhymes import get_all_seed_words
from engines.rhyme import compute_rhyme_group
from engines.syllable import count_word_syllables


def seed_rhymes(db_session):
    """Seed rhyme words. Idempotent - skips existing words."""
    words = get_all_seed_words()
    added = 0
    skipped = 0

    for word, theme in words:
        existing = db_session.query(Rhyme).filter_by(word=word).first()
        if existing:
            skipped += 1
            continue

        rhyme_group = compute_rhyme_group(word)
        syllable_count = count_word_syllables(word)

        rhyme = Rhyme(
            word=word,
            rhyme_group=rhyme_group,
            syllable_count=syllable_count,
            theme=theme,
            phonetic_ending=rhyme_group,
        )
        db_session.add(rhyme)
        added += 1

    db_session.commit()
    return added, skipped


def main():
    # Create all tables
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        added, skipped = seed_rhymes(db)
        total = db.query(Rhyme).count()
        print(f"Seed complete: {added} added, {skipped} skipped, {total} total rhymes in DB")

        # Verify all rows have rhyme_group
        empty_groups = db.query(Rhyme).filter(
            (Rhyme.rhyme_group == None) | (Rhyme.rhyme_group == "")
        ).count()
        print(f"Rows with empty rhyme_group: {empty_groups}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
