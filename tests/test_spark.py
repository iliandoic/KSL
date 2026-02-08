import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.connection import Base
from database.models import RhymeableWord
from engines.spark import generate_titles, generate_opening_lines, random_spark, word_explosion
from engines.rhyme import compute_rhyme_group


def get_test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    # Add some test rhymes
    words = [("нощ", "party"), ("мощ", "flex"), ("помощ", "loyalty")]
    for word, theme in words:
        db.add(RhymeableWord(word=word, rhyme_group=compute_rhyme_group(word), theme=theme))
    db.commit()
    return db


@patch("engines.spark.generate_with_prompt")
def test_generate_titles(mock_gen):
    mock_gen.return_value = "\n".join(
        [f"{i}. Заглавие {i}" for i in range(1, 11)]
    )
    result = generate_titles(theme="money")
    assert isinstance(result, list)
    assert len(result) <= 10
    # Verify theme was passed in the prompt
    call_args = mock_gen.call_args
    assert "money" in call_args[0][1]


@patch("engines.spark.generate_with_prompt")
def test_generate_titles_no_theme(mock_gen):
    mock_gen.return_value = "1. Без тема\n2. Друго заглавие\n3. Трето"
    result = generate_titles()
    assert isinstance(result, list)
    assert len(result) >= 1


@patch("engines.spark.generate_with_prompt")
def test_generate_opening_lines(mock_gen):
    mock_gen.return_value = "1. Първи ред\n2. Втори ред\n3. Трети ред\n4. Четвърти\n5. Пети"
    result = generate_opening_lines("Кралят на нощта")
    assert isinstance(result, list)
    assert len(result) <= 5


@patch("engines.spark.generate_with_prompt")
def test_random_spark(mock_gen):
    mock_gen.return_value = "Някаква вдъхновяваща фраза"
    result = random_spark()
    assert "spark" in result
    assert "type" in result
    assert result["type"] in ("line", "concept", "phrase")
    assert isinstance(result["spark"], str)
    assert len(result["spark"]) > 0


@patch("engines.spark.generate_with_prompt")
def test_word_explosion(mock_gen):
    mock_gen.return_value = """РЕДОВЕ ЗАПОЧВАЩИ С "нощ":
1. Нощта е моя
2. Нощ без край
3. Нощта пада тихо
4. Нощем блестя
5. Нощта ме вика

РЕДОВЕ ЗАВЪРШВАЩИ С "нощ":
1. Сам в тази нощ
2. Идва дълга нощ
3. Не спя цяла нощ
4. Огън в тази нощ
5. Крал на всяка нощ

НЕОЧАКВАНИ КОМБИНАЦИИ:
1. нощ от диаманти
2. нощен император
3. нощта плаче злато
4. нощен рапър
5. нощта танцува"""

    db = get_test_db()
    result = word_explosion("нощ", db)

    assert "starts_with" in result
    assert "ends_with" in result
    assert "rhymes" in result
    assert "combos" in result

    assert len(result["starts_with"]) > 0
    assert len(result["ends_with"]) > 0
    assert len(result["combos"]) > 0
    # Rhymes come from DB - should find "мощ" and "помощ"
    assert len(result["rhymes"]) >= 1
    db.close()


@patch("engines.spark.generate_with_prompt")
def test_word_explosion_no_db(mock_gen):
    mock_gen.return_value = """РЕДОВЕ ЗАПОЧВАЩИ С "тест":
1. Тест ред

РЕДОВЕ ЗАВЪРШВАЩИ С "тест":
1. Друг тест

НЕОЧАКВАНИ КОМБИНАЦИИ:
1. тест комбо"""

    result = word_explosion("тест", db=None)
    assert result["rhymes"] == []  # No DB = no rhymes
    assert len(result["starts_with"]) >= 1
