"""
Style analyzer - extracts patterns from user's lyrics.
Vocabulary frequency, rhyme patterns, average syllable count.
"""
import re
import hashlib
from collections import Counter

from sqlalchemy.orm import Session

from database.models import StylePattern
from engines.syllable import count_syllables
from engines.rhyme import compute_rhyme_group


def analyze_text(text: str) -> dict:
    """
    Analyze a text and extract style patterns.
    Returns dict with vocabulary, rhyme_patterns, avg_syllables.
    """
    if not text or not text.strip():
        return {"vocabulary": {}, "rhyme_patterns": [], "avg_syllables": 0}

    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]

    # Vocabulary frequency
    all_words = []
    for line in lines:
        words = re.findall(r"[\w]+", line.lower())
        all_words.extend(words)

    word_freq = Counter(all_words)
    # Top 30 words (excluding very short common words)
    common_short = {"и", "в", "на", "за", "от", "с", "да", "не", "е", "а", "но", "ме", "те", "се"}
    vocab = {
        word: count
        for word, count in word_freq.most_common(50)
        if word not in common_short and len(word) > 1
    }
    vocab = dict(list(vocab.items())[:30])

    # Rhyme patterns - extract endings of each line
    rhyme_patterns = []
    for line in lines:
        words = line.strip().split()
        if words:
            last_word = re.sub(r"[^\w]", "", words[-1])
            if last_word:
                ending = compute_rhyme_group(last_word)
                rhyme_patterns.append(ending)

    # Average syllable count per line
    syllable_counts = [count_syllables(line) for line in lines]
    avg_syllables = round(sum(syllable_counts) / len(syllable_counts), 1) if syllable_counts else 0

    return {
        "vocabulary": vocab,
        "rhyme_patterns": rhyme_patterns,
        "avg_syllables": avg_syllables,
    }


def store_style_patterns(
    text: str,
    analysis: dict,
    db: Session,
    user_id: str = "default",
) -> int:
    """Store analyzed style patterns in the DB. Returns number of patterns stored."""
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    # Check if already analyzed
    existing = db.query(StylePattern).filter_by(
        source_text_hash=text_hash, user_id=user_id
    ).first()
    if existing:
        return 0  # Already stored

    stored = 0

    # Store vocabulary frequencies
    for word, freq in analysis.get("vocabulary", {}).items():
        pattern = StylePattern(
            user_id=user_id,
            pattern_type="vocab_freq",
            key=word,
            value=float(freq),
            source_text_hash=text_hash,
        )
        db.add(pattern)
        stored += 1

    # Store average syllables
    avg_syl = analysis.get("avg_syllables", 0)
    if avg_syl > 0:
        pattern = StylePattern(
            user_id=user_id,
            pattern_type="avg_syllables",
            key="avg_syllables_per_line",
            value=float(avg_syl),
            source_text_hash=text_hash,
        )
        db.add(pattern)
        stored += 1

    # Store rhyme pattern summary
    rhyme_patterns = analysis.get("rhyme_patterns", [])
    if rhyme_patterns:
        rhyme_freq = Counter(rhyme_patterns)
        for rp, count in rhyme_freq.most_common(10):
            if rp:
                pattern = StylePattern(
                    user_id=user_id,
                    pattern_type="rhyme_pattern",
                    key=rp,
                    value=float(count),
                    source_text_hash=text_hash,
                )
                db.add(pattern)
                stored += 1

    db.commit()
    return stored


def get_style_context(db: Session, user_id: str = "default") -> str:
    """Build a style context string for injection into Claude prompts."""
    patterns = db.query(StylePattern).filter_by(user_id=user_id).all()
    if not patterns:
        return ""

    # Gather vocab
    vocab_items = [
        (p.key, p.value) for p in patterns if p.pattern_type == "vocab_freq"
    ]
    vocab_items.sort(key=lambda x: x[1], reverse=True)
    top_vocab = [word for word, _ in vocab_items[:10]]

    # Gather avg syllables
    avg_syl = next(
        (p.value for p in patterns if p.pattern_type == "avg_syllables"), None
    )

    parts = []
    if top_vocab:
        parts.append(f"Често използвани думи: {', '.join(top_vocab)}")
    if avg_syl:
        parts.append(f"Среден брой срички на ред: {avg_syl}")

    return "\n".join(parts)
