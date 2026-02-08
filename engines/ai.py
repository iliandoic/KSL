"""
Claude API integration with specialized prompts for Bulgarian chalga/trap lyrics.
"""
import re
from anthropic import Anthropic

from config import settings

SYSTEM_PROMPT = """Ти си експертен автор на текстове за българска чалга и трап музика.
Пишеш САМО на български език, използвайки кирилица.

Правила:
1. Всеки ред трябва да звучи естествено на български
2. Използвай рими, които работят фонетично на български
3. Спазвай стила на жанра - дързък, уличен, емоционален
4. Избягвай клишета - бъди оригинален и специфичен
5. Всеки ред трябва да може да се пее/рапира с ритъм

Когато ти дам тема, пиши в контекста на тази тема.
Когато ти дам стил, имитирай неговите характеристики.
Когато ти дам съществуващи редове, продължи естествено от тях.

ВАЖНО: Пиши САМО на кирилица. Никакъв латински текст освен имена на брандове."""

COMPLETION_PROMPT_TEMPLATE = """Дадени са следните редове от песен:
{lines}

{theme_context}
{style_context}
{corpus_context}

Напиши {count} възможни следващи реда. Всеки ред трябва:
- Да се римува с предходния ред
- Да има подобен брой срички ({syllable_target} ±2)
- Да продължава смислово от контекста

Формат: Напиши само редовете, по един на ред, номерирани (1. 2. 3. и т.н.)"""


def _get_client() -> Anthropic:
    return Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def _has_cyrillic(text: str) -> bool:
    """Check if text contains Cyrillic characters."""
    return bool(re.search(r"[\u0400-\u04FF]", text))


def _parse_numbered_lines(text: str) -> list[str]:
    """Parse numbered list format like '1. ...\n2. ...\n3. ...'."""
    lines = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # Remove numbering prefix like "1. ", "2) ", "- "
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", line)
        cleaned = re.sub(r"^[-•]\s*", "", cleaned)
        if cleaned:
            lines.append(cleaned)
    return lines


def complete_lines(
    lines: list[str],
    theme: str | None = None,
    style_context: str = "",
    corpus_context: str = "",
    count: int = 3,
    syllable_target: int | None = None,
) -> list[str]:
    """
    Generate line completions using Claude.
    Returns list of suggested next lines.
    """
    client = _get_client()

    lines_text = "\n".join(lines)

    theme_ctx = f"Тема: {theme}" if theme else ""
    style_ctx = f"Стил на автора:\n{style_context}" if style_context else ""
    corpus_ctx = f"Примерни редове за вдъхновение:\n{corpus_context}" if corpus_context else ""
    syl_target = syllable_target or 8

    prompt = COMPLETION_PROMPT_TEMPLATE.format(
        lines=lines_text,
        theme_context=theme_ctx,
        style_context=style_ctx,
        corpus_context=corpus_ctx,
        count=count,
        syllable_target=syl_target,
    )

    response = client.messages.create(
        model=settings.AI_MODEL,
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    result_text = response.content[0].text
    suggestions = _parse_numbered_lines(result_text)

    # Validate: at least some Cyrillic content
    valid = [s for s in suggestions if _has_cyrillic(s)]

    # If all filtered out, return raw (Claude might have used a different format)
    return valid if valid else suggestions[:count]


def generate_with_prompt(
    system: str,
    user_prompt: str,
    max_tokens: int = 800,
) -> str:
    """Generic Claude call with custom system/user prompts. Used by spark engine."""
    client = _get_client()
    response = client.messages.create(
        model=settings.AI_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text
