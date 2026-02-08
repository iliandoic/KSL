"""
Theme templates for auto-detecting lyrics themes via keyword matching.
5 core themes with keywords and mood descriptors.
"""

THEMES = {
    "money": {
        "keywords": [
            "пари", "кеш", "лари", "милион", "богат", "злато", "златен",
            "банка", "печалба", "бизнес", "скъп", "евро", "долар", "хиляда",
            "капитал", "лукс", "диамант", "мерцедес", "ролекс", "вила",
            "харча", "купувам", "плащам", "трупам", "печеля", "хвърлям",
            # Multi-language keywords (Bosnian/Serbian/Romanian/English/French)
            "money", "cash", "rich", "gold", "diamond", "million",
            "pare", "novac", "bani", "bogat", "argent", "riche",
        ],
        "mood": "confident, flashy, dominant",
    },
    "love": {
        "keywords": [
            "любов", "сърце", "целувка", "обич", "страст", "желание",
            "мечта", "ангел", "красива", "очи", "устни", "душа",
            "огън", "пламък", "луна", "звезда", "роза", "цвете",
            "обичам", "целувам", "копнея", "горя", "шептя",
            # Multi-language
            "love", "heart", "kiss", "passion", "dream", "angel",
            "ljubav", "srce", "poljubac", "dragoste", "inima", "amour", "coeur",
        ],
        "mood": "romantic, passionate, vulnerable",
    },
    "enemies": {
        "keywords": [
            "враг", "омраза", "завист", "предател", "измама", "лъжа",
            "змия", "отрова", "нож", "битка", "война", "победа",
            "гняв", "сила", "мощ", "власт", "страх", "отмъщение",
            "мразя", "унищожавам", "разбивам", "побеждавам",
            # Multi-language
            "enemy", "hate", "envy", "traitor", "revenge", "power",
            "neprijatelj", "mrznja", "osveta", "dusman", "ennemi", "haine",
        ],
        "mood": "aggressive, threatening, dominant",
    },
    "party": {
        "keywords": [
            "парти", "клуб", "дискотека", "бар", "бутилка", "уиски",
            "водка", "шампанско", "танц", "ритъм", "бийт", "музика",
            "нощ", "купон", "веселба", "адреналин", "кеф",
            "танцувам", "пия", "лудувам", "скачам", "крещя", "пея",
            # Multi-language
            "party", "club", "dance", "drink", "night", "fun",
            "zurka", "noć", "ples", "petrecere", "noapte", "fête", "nuit",
        ],
        "mood": "energetic, wild, euphoric",
    },
    "street": {
        "keywords": [
            "улица", "квартал", "блок", "гето", "махала", "асфалт",
            "полиция", "закон", "гангстер", "мафия", "бос", "банда",
            "оръжие", "куршум", "бягам", "крия", "оцелявам",
            "тежко", "жестоко", "реално", "живот", "съдба",
            # Multi-language
            "street", "hood", "block", "ghetto", "gang", "police", "gun",
            "ulica", "kvart", "stradă", "cartier", "rue", "quartier",
        ],
        "mood": "raw, gritty, survival",
    },
}


def detect_theme(text: str) -> str | None:
    """Detect the primary theme of a text line via keyword matching."""
    text_lower = text.lower()
    scores = {}
    for theme, data in THEMES.items():
        score = sum(1 for kw in data["keywords"] if kw in text_lower)
        if score > 0:
            scores[theme] = score

    if not scores:
        return None
    return max(scores, key=scores.get)


def get_theme_mood(theme: str) -> str:
    """Get the mood descriptor for a theme."""
    if theme in THEMES:
        return THEMES[theme]["mood"]
    return ""


def get_all_themes() -> list[str]:
    """Return list of all theme names."""
    return list(THEMES.keys())
