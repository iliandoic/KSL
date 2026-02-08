"""
Spark Generator - solves the blank page problem.
3 modes: Title First, Random Spark, Word Explosion.
"""
import random

from engines.ai import generate_with_prompt, _parse_numbered_lines
from engines.rhyme import find_rhymes
from sqlalchemy.orm import Session

SPARK_SYSTEM = """Ти си креативен автор на текстове за българска чалга и трап музика.
Специализираш се в това да генерираш вдъхновяващи начални идеи за песни.

Правила:
1. Пиши САМО на български (кирилица)
2. Бъди изненадващ - избягвай очевидното
3. Бъди специфичен - конкретни образи, не абстракции
4. Всяко предложение трябва да е уникално и запомнящо се
5. Пиши в стила на модерна българска чалга/трап"""


def generate_titles(theme: str | None = None) -> list[str]:
    """Generate 10 potential song titles."""
    theme_part = f' на тема "{theme}"' if theme else ""
    prompt = f"""Измисли 10 заглавия за българска чалга/трап песен{theme_part}.

Заглавията трябва да са:
- Кратки (2-5 думи)
- Запомнящи се и провокативни
- В стила на модерна чалга/трап
- Различни едно от друго

Формат: Номериран списък (1. 2. 3. ... 10.)"""

    result = generate_with_prompt(SPARK_SYSTEM, prompt)
    titles = _parse_numbered_lines(result)
    return titles[:10]


def generate_opening_lines(title: str) -> list[str]:
    """Generate 5 opening lines for a given title."""
    prompt = f"""Заглавието на песента е: "{title}"

Напиши 5 различни варианта за първи ред на тази песен.
Всеки ред трябва:
- Да хваща вниманието веднага
- Да задава тона и настроението на песента
- Да е между 6 и 12 срички
- Да звучи като нещо, което реално би се пяло/рапирало

Формат: Номериран списък (1. 2. 3. 4. 5.)"""

    result = generate_with_prompt(SPARK_SYSTEM, prompt)
    lines = _parse_numbered_lines(result)
    return lines[:5]


def random_spark() -> dict:
    """Generate a random creative spark."""
    spark_types = ["line", "concept", "phrase"]
    spark_type = random.choice(spark_types)

    prompts = {
        "line": """Измисли 1 оригинален ред за българска чалга/трап песен.
Трябва да е изненадващ, конкретен и запомнящ се.
Напиши САМО реда, без обяснения.""",
        "concept": """Измисли 1 необичайна концепция/идея за българска чалга/трап песен.
Примери за формат: "Песен за [нещо неочаквано]", "Какво ако [абсурдна ситуация]"
Напиши САМО концепцията, без обяснения.""",
        "phrase": """Измисли 1 силна фраза/пънчлайн за българска чалга/трап песен.
Трябва да е от типа ред, който хората цитират.
Напиши САМО фразата, без обяснения.""",
    }

    result = generate_with_prompt(SPARK_SYSTEM, prompts[spark_type], max_tokens=200)
    # Clean up - take first non-empty line
    spark_text = result.strip().split("\n")[0].strip()
    # Remove quotes if present
    spark_text = spark_text.strip('"').strip("'").strip("«").strip("»")

    return {"spark": spark_text, "type": spark_type}


def word_explosion(word: str, db: Session | None = None) -> dict:
    """
    Explode a single word into creative directions.
    Returns lines starting with it, ending with it, rhymes, and unexpected combos.
    """
    prompt = f"""Думата е: "{word}"

Генерирай:

РЕДОВЕ ЗАПОЧВАЩИ С "{word}":
(5 реда за песен, всеки започващ с тази дума)

РЕДОВЕ ЗАВЪРШВАЩИ С "{word}":
(5 реда за песен, всеки завършващ с тази дума)

НЕОЧАКВАНИ КОМБИНАЦИИ:
(5 необичайни словосъчетания с тази дума)

Формат: Следвай точно тези секции с номерирани списъци."""

    result = generate_with_prompt(SPARK_SYSTEM, prompt, max_tokens=800)

    # Parse sections
    starts_with = []
    ends_with = []
    combos = []

    current_section = None
    for line in result.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        upper = line.upper()
        if "ЗАПОЧВАЩИ" in upper or "STARTING" in upper:
            current_section = "starts"
            continue
        elif "ЗАВЪРШВАЩИ" in upper or "ENDING" in upper:
            current_section = "ends"
            continue
        elif "КОМБИНАЦИИ" in upper or "COMBO" in upper:
            current_section = "combos"
            continue

        # Clean numbered prefix
        import re
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", line)
        cleaned = re.sub(r"^[-•]\s*", "", cleaned)
        if not cleaned:
            continue

        if current_section == "starts":
            starts_with.append(cleaned)
        elif current_section == "ends":
            ends_with.append(cleaned)
        elif current_section == "combos":
            combos.append(cleaned)

    # Get rhymes from DB if available
    rhymes_list = []
    if db:
        rhyme_result = find_rhymes(word, db, limit=10)
        rhymes_list = rhyme_result["perfect"] + rhyme_result["near"] + rhyme_result["slant"]
        rhymes_list = rhymes_list[:10]

    return {
        "starts_with": starts_with[:5],
        "ends_with": ends_with[:5],
        "rhymes": rhymes_list,
        "combos": combos[:5],
    }
