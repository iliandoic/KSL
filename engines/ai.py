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


def _parse_numbered_lines(text: str, expected_count: int = 0) -> list[str]:
    """Parse numbered list format like '1. ...\n2. ...\n3. ...'.
    If expected_count > 0, returns list of that size with items in correct positions.
    """
    if expected_count > 0:
        # Parse by line number to handle out-of-order responses
        result = [""] * expected_count
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            # Match "1. text" or "1) text"
            match = re.match(r"^(\d+)[\.\)]\s*(.+)$", line)
            if match:
                num = int(match.group(1)) - 1  # 0-indexed
                content = match.group(2).strip()
                if 0 <= num < expected_count:
                    result[num] = content
        return result
    else:
        # Original behavior for backwards compatibility
        lines = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
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


def group_rhyme_endings(endings: list[str]) -> dict[str, list[str]]:
    """
    Group rhyme endings by sound using AI.
    Returns dict like {"EE": ["-eri", "-elly", "-eady"], "OT": ["-ot", "-ote"]}.
    Original spellings are preserved.
    """
    if not endings:
        return {}

    client = _get_client()

    system = """You are a phonetics expert. Group these word endings by rhyme sound.
Return ONLY valid JSON with group names as keys and arrays of endings as values.
Keep the original spelling of each ending exactly as provided.
Group names should be simple phonetic labels like "EE", "OT", "AY", "ATE", etc."""

    user_prompt = f"""Group these endings by rhyme sound:
{', '.join(endings)}

Return JSON only, example format:
{{"EE": ["-eri", "-elly"], "OT": ["-ot", "-ote"]}}"""

    response = client.messages.create(
        model=settings.AI_MODEL,
        max_tokens=500,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )

    result_text = response.content[0].text.strip()

    # Parse JSON from response
    import json
    try:
        # Try to extract JSON from response
        json_match = re.search(r'\{[^{}]*\}', result_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(result_text)
    except json.JSONDecodeError:
        # Fallback: put all endings in one group
        return {"OTHER": endings}


def extract_concepts(lyrics: str) -> list[str]:
    """
    Extract 3-5 high-level concepts from translated lyrics.
    Returns actionable themes like "proving haters wrong", not single words.
    """
    if not lyrics or not lyrics.strip():
        return []

    client = _get_client()

    system = """Extract the main concepts/themes from these song lyrics.
Return 3-5 actionable concepts, not single words.
Good examples: "proving haters wrong", "self-made success", "revenge on the ex", "luxury lifestyle"
Bad examples: "love", "money", "success" (too generic)
Return ONLY a JSON array of strings."""

    response = client.messages.create(
        model=settings.AI_MODEL,
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": f"Extract concepts from:\n\n{lyrics}"}],
    )

    result_text = response.content[0].text.strip()

    import json
    try:
        # Try to extract JSON array from response
        json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(result_text)
    except json.JSONDecodeError:
        return []


def generate_prompts(concepts: list[str]) -> list[str]:
    """
    Turn concepts into freestyle questions/prompts.
    Example: "proving haters wrong" -> "Who doubted you?"
    """
    if not concepts:
        return []

    client = _get_client()

    system = """Turn these concepts into freestyle questions that a rapper can answer.
Make them personal, direct, and inspiring.
Good examples: "Who doubted you?", "What would you do with a million?", "What's your revenge fantasy?"
Return ONLY a JSON array of strings."""

    response = client.messages.create(
        model=settings.AI_MODEL,
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": f"Turn these concepts into questions:\n{concepts}"}],
    )

    result_text = response.content[0].text.strip()

    import json
    try:
        json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(result_text)
    except json.JSONDecodeError:
        return []


def translate_lines(lines: list[str], target_lang: str = "en", model: str = "sonnet") -> list[str]:
    """
    Translate lines using Claude with prefill trick.
    """
    if not lines:
        return []

    client = _get_client()

    if target_lang == "bg":
        lang_instruction = "Bulgarian (use Cyrillic script)"
    else:
        lang_instruction = "English"

    system = """Expert translator for song lyrics. Preserve:
- Slang and street language feel
- Emotional tone and attitude
- Rhyme patterns when possible
Output only numbered translations, nothing else."""

    model_id = "claude-opus-4-5-20251101" if model == "opus" else "claude-sonnet-4-20250514"

    response = client.messages.create(
        model=model_id,
        max_tokens=1000,
        system=system,
        messages=[
            {"role": "user", "content": f"Translate to {lang_instruction}:\n" + "\n".join(f"{i+1}. {l}" for i, l in enumerate(lines))},
            {"role": "assistant", "content": "1."}
        ],
    )

    result_text = "1." + response.content[0].text
    translations = _parse_numbered_lines(result_text, expected_count=len(lines))

    return translations
