import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.connection import Base
from database.models import RhymeableWord
from engines.rhyme import extract_phonetic_ending, find_rhymes, compute_rhyme_group


def get_test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_devoicing_lyubov_gotov():
    """любов and готов should have the same rhyme_group (в→ф devoicing)."""
    r1 = extract_phonetic_ending("любов")
    r2 = extract_phonetic_ending("готов")
    assert r1["rhyme_group"] == r2["rhyme_group"]
    assert "ф" in r1["consonant_frame"]  # в devoiced to ф


def test_devoicing_vrag():
    """враг should devoice г→к."""
    r = extract_phonetic_ending("враг")
    assert "к" in r["consonant_frame"]


def test_vowel_groups_maya_staya():
    """мая and стая should match - я is in A group."""
    r1 = extract_phonetic_ending("мая")
    r2 = extract_phonetic_ending("стая")
    assert r1["vowel_class"] == r2["vowel_class"] == "A"
    # Both have adjacent vowel before я, should get same rhyme_group
    assert r1["rhyme_group"] == r2["rhyme_group"]


def test_banitsa_ulitsa_match():
    """баница and улица should be perfect rhymes (-ица ending)."""
    r1 = extract_phonetic_ending("баница")
    r2 = extract_phonetic_ending("улица")
    assert r1["rhyme_group"] == r2["rhyme_group"]
    # The key should include 'ц' as the bridge consonant
    assert "ц" in r1["rhyme_group"]


def test_banitsa_smetka_no_match():
    """баница and сметка should NOT be perfect rhymes."""
    r1 = extract_phonetic_ending("баница")
    r2 = extract_phonetic_ending("сметка")
    assert r1["rhyme_group"] != r2["rhyme_group"]


def test_vowel_ending_precision():
    """Words ending in -ка, -ца, -та should get different rhyme_groups."""
    rg_ka = compute_rhyme_group("банка")    # -ка
    rg_tsa = compute_rhyme_group("баница")  # -ца
    rg_ta = compute_rhyme_group("врата")    # -та
    assert rg_ka != rg_tsa
    assert rg_ka != rg_ta
    assert rg_tsa != rg_ta


def test_consonant_ending_still_works():
    """Words ending in consonants should still match correctly."""
    assert compute_rhyme_group("враг") == compute_rhyme_group("мрак")  # both -ак → A:к
    assert compute_rhyme_group("нощ") == compute_rhyme_group("мощ")    # both -ощ → O:щ


def test_find_rhymes_with_db():
    """find_rhymes should return categorized results."""
    db = get_test_db()
    words = [
        RhymeableWord(word="пари", rhyme_group=compute_rhyme_group("пари")),
        RhymeableWord(word="вари", rhyme_group=compute_rhyme_group("вари")),
        RhymeableWord(word="стари", rhyme_group=compute_rhyme_group("стари")),
        RhymeableWord(word="цари", rhyme_group=compute_rhyme_group("цари")),
        RhymeableWord(word="море", rhyme_group=compute_rhyme_group("море")),
    ]
    db.add_all(words)
    db.commit()

    result = find_rhymes("пари", db)
    assert "perfect" in result
    assert "near" in result
    assert "slant" in result
    # вари, стари, цари should be perfect rhymes for пари (all -ри ending)
    assert len(result["perfect"]) >= 2
    # море should NOT be a perfect rhyme
    assert "море" not in result["perfect"]
    db.close()


def test_find_rhymes_no_false_positives():
    """баница should NOT perfectly rhyme with банка or сметка."""
    db = get_test_db()
    words = [
        RhymeableWord(word="улица", rhyme_group=compute_rhyme_group("улица")),
        RhymeableWord(word="банка", rhyme_group=compute_rhyme_group("банка")),
        RhymeableWord(word="сметка", rhyme_group=compute_rhyme_group("сметка")),
        RhymeableWord(word="столица", rhyme_group=compute_rhyme_group("столица")),
    ]
    db.add_all(words)
    db.commit()

    result = find_rhymes("баница", db)
    assert "улица" in result["perfect"]
    assert "столица" in result["perfect"]
    assert "банка" not in result["perfect"]
    assert "сметка" not in result["perfect"]
    db.close()


def test_unknown_word_no_error():
    """Unknown word not in DB should still be analyzed without error."""
    db = get_test_db()
    result = find_rhymes("непознатадума", db)
    assert "perfect" in result
    assert "near" in result
    assert "slant" in result
    db.close()


def test_empty_input():
    """Empty input should return empty results."""
    db = get_test_db()
    result = find_rhymes("", db)
    assert result == {"perfect": [], "near": [], "slant": []}
    db.close()


def test_phonetic_ending_empty():
    r = extract_phonetic_ending("")
    assert r["rhyme_group"] == ""


def test_vowel_class_mapping():
    """Verify vowel class mappings."""
    assert extract_phonetic_ending("мъка")["vowel_class"] == "A"  # last vowel is а → A
    assert extract_phonetic_ending("юг")["vowel_class"] == "U"   # ю → U
    assert extract_phonetic_ending("мед")["vowel_class"] == "E"   # е → E


def test_er_golyamo_separate():
    """ъ should NOT match а — влак should not rhyme with данък."""
    rg_vlak = compute_rhyme_group("влак")    # -ак → A:к
    rg_danak = compute_rhyme_group("данък")  # -ък → Y:к
    assert rg_vlak != rg_danak
    # But данък and пламък should match (both -ък)
    rg_plamak = compute_rhyme_group("пламък")
    assert rg_danak == rg_plamak
