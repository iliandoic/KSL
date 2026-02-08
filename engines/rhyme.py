import re
from sqlalchemy.orm import Session

from database.models import RhymeableWord

# Word-final devoicing map (Bulgarian phonetics)
DEVOICING = {
    "б": "п",
    "в": "ф",
    "г": "к",
    "д": "т",
    "ж": "ш",
    "з": "с",
}

# Vowel equivalence groups for rhyming
VOWEL_GROUPS = {
    "а": "A", "я": "A",   # я = йа, contains а sound
    "ъ": "Y",              # ъ is a distinct mid-central vowel, NOT like а
    "у": "U", "ю": "U",   # ю = йу, contains у sound
    "е": "E",
    "и": "I",
    "о": "O",
}

BG_VOWELS = set("аеиоуъяю")


def _clean_word(word: str) -> str:
    """Lowercase and strip non-Cyrillic."""
    return re.sub(r"[^а-яёА-ЯЁ]", "", word).lower()


def _apply_devoicing(consonants: str) -> str:
    """Apply word-final devoicing to consonant cluster."""
    return "".join(DEVOICING.get(c, c) for c in consonants)


def _get_vowel_class(vowel: str) -> str:
    """Map a vowel to its equivalence class."""
    return VOWEL_GROUPS.get(vowel, vowel.upper())


def extract_phonetic_ending(word: str) -> dict:
    """
    Extract the phonetic ending for rhyme matching.

    For words ending in consonant(s) (e.g. "любов" → -ов → -оф):
        rhyme_group = "vowel_class:devoiced_trailing"  e.g. "O:ф"

    For words ending in a vowel (e.g. "баница" → -ца):
        Include the preceding consonant (or preceding vowel class if adjacent vowels)
        to avoid collapsing all vowel-ending words into one bucket.
        rhyme_group = "pre_char + vowel_class:"  e.g. "цA:"

    Returns: {"ending", "rhyme_group", "vowel_class", "consonant_frame"}
    """
    clean = _clean_word(word)
    if not clean:
        return {"ending": "", "rhyme_group": "", "vowel_class": "", "consonant_frame": ""}

    # Find all vowel positions
    vowel_positions = [i for i, c in enumerate(clean) if c in BG_VOWELS]

    if not vowel_positions:
        # No vowels found (e.g. "DJ")
        return {"ending": clean, "rhyme_group": f":{clean}", "vowel_class": "", "consonant_frame": clean}

    last_vowel_idx = vowel_positions[-1]
    last_vowel = clean[last_vowel_idx]
    trailing = clean[last_vowel_idx + 1:]

    # Apply devoicing to trailing consonants
    devoiced_trailing = _apply_devoicing(trailing)

    vowel_class = _get_vowel_class(last_vowel)
    consonant_frame = devoiced_trailing

    # Build rhyme_group key
    if devoiced_trailing:
        # Word ends in consonant(s): "любов" → "O:ф", "враг" → "A:к"
        rhyme_group = f"{vowel_class}:{devoiced_trailing}"
    else:
        # Word ends in a vowel — include preceding character for precision
        # This prevents ALL words ending in 'а' from matching each other
        pre = ""
        if last_vowel_idx > 0:
            prev_char = clean[last_vowel_idx - 1]
            if prev_char in BG_VOWELS:
                # Adjacent vowels (e.g. "мая" → prev is 'а'): use vowel class
                pre = _get_vowel_class(prev_char)
            else:
                # Preceding consonant (e.g. "баница" → prev is 'ц'): use devoiced form
                pre = DEVOICING.get(prev_char, prev_char)
        rhyme_group = f"{pre}{vowel_class}:"

    return {
        "ending": clean[last_vowel_idx:],
        "rhyme_group": rhyme_group,
        "vowel_class": vowel_class,
        "consonant_frame": consonant_frame,
    }


def compute_rhyme_group(word: str) -> str:
    """Convenience: return just the rhyme_group string."""
    return extract_phonetic_ending(word)["rhyme_group"]


def find_rhymes(word: str, db: Session, limit: int = 20) -> dict:
    """
    Find rhymes for a word using 3-tier matching.
    Returns {"perfect": [...], "near": [...], "slant": [...]}

    Works even if the input word is not in the DB (on-the-fly analysis).
    """
    if not word or not word.strip():
        return {"perfect": [], "near": [], "slant": []}

    info = extract_phonetic_ending(word)
    rhyme_group = info["rhyme_group"]
    vowel_class = info["vowel_class"]
    consonant_frame = info["consonant_frame"]
    clean_input = _clean_word(word)

    if not rhyme_group:
        return {"perfect": [], "near": [], "slant": []}

    perfect = []
    near = []
    slant = []

    # Query all rhymeable words from DB
    all_rhymes = db.query(RhymeableWord).all()

    for r in all_rhymes:
        if _clean_word(r.word) == clean_input:
            continue  # Skip the word itself

        r_info = extract_phonetic_ending(r.word)
        r_group = r_info["rhyme_group"]
        r_vowel = r_info["vowel_class"]
        r_consonant = r_info["consonant_frame"]

        if r_group == rhyme_group:
            # Exact rhyme_group match → perfect rhyme
            perfect.append(r.word)
        elif r_vowel == vowel_class and r_consonant == consonant_frame:
            # Same vowel class + same trailing consonants but different bridge → near
            near.append(r.word)
        elif r_consonant == consonant_frame and r_consonant:
            # Same trailing consonant pattern, different vowel → slant
            slant.append(r.word)

    return {
        "perfect": perfect[:limit],
        "near": near[:limit],
        "slant": slant[:limit],
    }
