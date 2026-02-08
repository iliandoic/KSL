import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.syllable import count_syllables, count_word_syllables, syllable_breakdown


def test_lyubov():
    assert count_syllables("любов") == 2


def test_full_sentence():
    assert count_syllables("Имам пари да хвърлям") == 7


def test_natsiya():
    assert count_syllables("нация") == 3


def test_empty():
    assert count_syllables("") == 0


def test_no_vowel_word():
    # DJ has no Cyrillic/Latin vowels in standard form, min 1
    assert count_word_syllables("DJ") == 1


def test_hyphenated():
    # "черно-бяло" = черно(2) + бяло(2) = 4
    assert count_syllables("черно-бяло") == 4


def test_breakdown():
    result = syllable_breakdown("Имам пари")
    assert result["total"] == 4
    assert len(result["words"]) == 2
    assert result["words"][0]["word"] == "Имам"
    assert result["words"][0]["syllables"] == 2
    assert result["words"][1]["word"] == "пари"
    assert result["words"][1]["syllables"] == 2


def test_whitespace_only():
    assert count_syllables("   ") == 0


def test_latin_vowels():
    # For pasted Serbian/Romanian/English lyrics
    assert count_syllables("love") == 2  # l-o-v-e has 2 vowels
    assert count_syllables("money") >= 2
