import re

# Bulgarian vowels (lowercase) - each counts as 1 syllable
BG_VOWELS = set("аеиоуъяю")

# Extended vowel sets for other Slavic/Latin languages the user may paste
# Serbian/Bosnian Cyrillic vowels overlap with Bulgarian
# Romanian/French/English use Latin vowels
LATIN_VOWELS = set("aeiouyàâäéèêëïîôùûüœæ")


def count_syllables(text: str) -> int:
    """Count syllables in Bulgarian text. Returns total syllable count."""
    if not text or not text.strip():
        return 0
    words = text.strip().split()
    total = 0
    for word in words:
        total += count_word_syllables(word)
    return total


def count_word_syllables(word: str) -> int:
    """Count syllables in a single word. Minimum 1 for non-empty words."""
    if not word:
        return 0
    # Remove hyphens and split compound words
    parts = word.replace("-", " ").split()
    total = 0
    for part in parts:
        clean = re.sub(r"[^\w]", "", part).lower()
        if not clean:
            continue
        # Count vowels (both Cyrillic and Latin)
        vowel_count = sum(1 for ch in clean if ch in BG_VOWELS or ch in LATIN_VOWELS)
        # Minimum 1 syllable for non-empty words (e.g., "DJ", "MC")
        total += max(vowel_count, 1) if clean else 0
    return total


def syllable_breakdown(text: str) -> dict:
    """Return total count and per-word breakdown."""
    if not text or not text.strip():
        return {"total": 0, "words": []}
    words = text.strip().split()
    breakdown = []
    total = 0
    for word in words:
        count = count_word_syllables(word)
        breakdown.append({"word": word, "syllables": count})
        total += count
    return {"total": total, "words": breakdown}
