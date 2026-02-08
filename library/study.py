"""
Artist study module - extracts learning data from scraped songs.
Fills the inspiration pool with rhyme endings, vocabulary, concepts, prompts.
"""
import re
import json
from datetime import datetime

from sqlalchemy.orm import Session

from database.models import ArtistStudy, ArtistRhymeGroup, ScrapedSong
from engines.ai import group_rhyme_endings, extract_concepts, generate_prompts, translate_title
from library.themes import detect_theme


def extract_rhyme_ending(word: str) -> str:
    """
    Extract the rhyme ending from a word (any language).
    Returns last 2-4 characters as the ending.
    """
    word = word.strip().lower()
    # Remove punctuation from end
    word = re.sub(r'[^\w]+$', '', word)
    if not word:
        return ""
    # Take last 2-4 chars depending on word length
    if len(word) <= 3:
        return f"-{word}"
    elif len(word) <= 5:
        return f"-{word[-3:]}"
    else:
        return f"-{word[-4:]}"


def extract_endings_from_lyrics(lyrics: str) -> dict[str, int]:
    """
    Extract rhyme endings from lyrics (last word of each line).
    Returns dict of ending -> frequency count.
    """
    endings = {}
    for line in lyrics.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        # Skip section headers
        if re.match(r'^\[.*\]$', line):
            continue
        words = line.split()
        if words:
            last_word = words[-1]
            ending = extract_rhyme_ending(last_word)
            if ending:
                endings[ending] = endings.get(ending, 0) + 1
    return endings


def extract_vocabulary(text: str) -> dict[str, int]:
    """
    Extract Bulgarian words from translated text.
    Returns dict of word -> frequency count.
    """
    # Match Cyrillic words (3+ chars)
    words = re.findall(r'[а-яёА-ЯЁ]{3,}', text.lower())
    vocab = {}
    for word in words:
        vocab[word] = vocab.get(word, 0) + 1
    return vocab


def study_song(
    scraped_song: ScrapedSong,
    db: Session,
) -> dict:
    """
    Study a scraped song and update the artist's study data.
    Extracts rhyme endings, vocabulary, concepts, prompts.
    Returns summary of what was learned.
    """
    artist = scraped_song.artist
    if not artist:
        return {"error": "No artist specified"}

    # Get or create ArtistStudy
    study = db.query(ArtistStudy).filter_by(artist=artist).first()
    if not study:
        study = ArtistStudy(
            artist=artist,
            songs_studied=0,
            vocabulary_json="{}",
            concepts_json="[]",
            prompts_json="[]",
            titles_json="[]",
        )
        db.add(study)

    # Get translations (prefer sonnet, fall back to opus)
    translations_json = scraped_song.sonnet_translations_json or scraped_song.opus_translations_json
    if translations_json:
        try:
            translations = json.loads(translations_json)
            translated_text = "\n".join(translations.values())
        except json.JSONDecodeError:
            translated_text = ""
    else:
        translated_text = ""

    result = {
        "artist": artist,
        "title": scraped_song.title,
        "endings_added": 0,
        "vocabulary_added": 0,
        "concepts_added": 0,
        "prompts_added": 0,
    }

    # 1. Extract rhyme endings from ORIGINAL lyrics
    if scraped_song.original_text:
        endings = extract_endings_from_lyrics(scraped_song.original_text)
        if endings:
            # Get unique endings for AI grouping
            unique_endings = list(endings.keys())
            groups = group_rhyme_endings(unique_endings)

            # Update ArtistRhymeGroup entries
            for group_name, group_endings in groups.items():
                # Find or create group
                rhyme_group = db.query(ArtistRhymeGroup).filter_by(
                    artist=artist, group_name=group_name
                ).first()

                if not rhyme_group:
                    rhyme_group = ArtistRhymeGroup(
                        artist=artist,
                        group_name=group_name,
                        endings_json="[]",
                        example_words_json="{}",
                        frequency=0,
                    )
                    db.add(rhyme_group)

                # Merge endings
                existing = json.loads(rhyme_group.endings_json or "[]")
                for ending in group_endings:
                    if ending not in existing:
                        existing.append(ending)
                        result["endings_added"] += 1
                rhyme_group.endings_json = json.dumps(existing)

                # Update frequency
                freq_sum = sum(endings.get(e, 0) for e in group_endings)
                rhyme_group.frequency += freq_sum

    # 2. Add title (translated to Bulgarian)
    if scraped_song.title:
        bg_title = translate_title(scraped_song.title)
        existing_titles = json.loads(study.titles_json or "[]")
        if bg_title not in existing_titles:
            existing_titles.append(bg_title)
            study.titles_json = json.dumps(existing_titles, ensure_ascii=False)

    # 3. Extract vocabulary from translations
    if translated_text:
        new_vocab = extract_vocabulary(translated_text)
        existing_vocab = json.loads(study.vocabulary_json or "{}")
        for word, count in new_vocab.items():
            if word not in existing_vocab:
                result["vocabulary_added"] += 1
            existing_vocab[word] = existing_vocab.get(word, 0) + count
        study.vocabulary_json = json.dumps(existing_vocab, ensure_ascii=False)

    # 4. Extract concepts from translations
    if translated_text:
        new_concepts = extract_concepts(translated_text)
        existing_concepts = json.loads(study.concepts_json or "[]")
        for concept in new_concepts:
            if concept not in existing_concepts:
                existing_concepts.append(concept)
                result["concepts_added"] += 1
        study.concepts_json = json.dumps(existing_concepts, ensure_ascii=False)

    # 5. Generate prompts from new concepts
    if result["concepts_added"] > 0:
        new_concepts = extract_concepts(translated_text)  # Get fresh concepts for prompts
        new_prompts = generate_prompts(new_concepts)
        existing_prompts = json.loads(study.prompts_json or "[]")
        for prompt in new_prompts:
            if prompt not in existing_prompts:
                existing_prompts.append(prompt)
                result["prompts_added"] += 1
        study.prompts_json = json.dumps(existing_prompts, ensure_ascii=False)

    # Update counts
    study.songs_studied += 1
    study.updated_at = datetime.utcnow()

    db.commit()
    return result


def get_artist_study(artist: str, db: Session) -> dict | None:
    """Get full study data for an artist."""
    study = db.query(ArtistStudy).filter_by(artist=artist).first()
    if not study:
        return None

    # Get rhyme groups
    rhyme_groups = db.query(ArtistRhymeGroup).filter_by(artist=artist).all()

    return {
        "artist": study.artist,
        "songs_studied": study.songs_studied,
        "vocabulary": json.loads(study.vocabulary_json or "{}"),
        "concepts": json.loads(study.concepts_json or "[]"),
        "prompts": json.loads(study.prompts_json or "[]"),
        "titles": json.loads(study.titles_json or "[]"),
        "rhyme_groups": [
            {
                "group_name": rg.group_name,
                "endings": json.loads(rg.endings_json or "[]"),
                "example_words": json.loads(rg.example_words_json or "{}"),
                "frequency": rg.frequency,
            }
            for rg in rhyme_groups
        ],
    }


def get_all_studied_artists(db: Session) -> list[dict]:
    """Get list of all studied artists with song counts."""
    studies = db.query(ArtistStudy).order_by(ArtistStudy.songs_studied.desc()).all()
    return [
        {
            "artist": s.artist,
            "songs_studied": s.songs_studied,
        }
        for s in studies
    ]
