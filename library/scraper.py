"""
Genius lyrics scraper. Fetches lyrics from a Genius URL.
"""
import re
import urllib.request

from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Map section headers to normalized section types
SECTION_MAP = {
    # Hooks/Chorus
    'refren': 'hook',
    'chorus': 'hook',
    'hook': 'hook',
    'припев': 'hook',  # Russian/Bulgarian
    # Pre-chorus
    'pre-refren': 'pre-hook',
    'pre-chorus': 'pre-hook',
    'prechorus': 'pre-hook',
    # Verses
    'verse': 'verse',
    'strofa': 'verse',
    'vers': 'verse',
    'куплет': 'verse',  # Russian
    # Bridge
    'bridge': 'bridge',
    'pod': 'bridge',
    'мост': 'bridge',
    # Intro/Outro
    'intro': 'intro',
    'outro': 'outro',
    # Post-chorus
    'post-chorus': 'post-hook',
    'post-refren': 'post-hook',
}


def _normalize_section(header: str) -> str | None:
    """Convert a section header like '[Refren]' to a normalized type."""
    # Remove brackets and clean up
    clean = header.strip('[]').lower()
    # Remove numbers like "Verse 1" -> "verse"
    clean = re.sub(r'\s*\d+\s*', '', clean)
    # Remove parenthetical content like "(x2)"
    clean = re.sub(r'\s*\(.*?\)\s*', '', clean)
    clean = clean.strip()

    # Check direct match
    if clean in SECTION_MAP:
        return SECTION_MAP[clean]

    # Check if it starts with any known section
    for key, val in SECTION_MAP.items():
        if clean.startswith(key):
            return val

    return None


def scrape_genius(url: str) -> dict:
    """
    Scrape lyrics from a Genius URL.
    Returns {"title": str, "artist": str, "lyrics": str, "sections": list}

    sections is a list of {"section": str, "lines": list[str]}
    """
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode("utf-8")

    soup = BeautifulSoup(html, "html.parser")

    # Extract title/artist from page
    title_tag = soup.select_one("h1[class*='SongHeader']") or soup.select_one("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""

    artist_tag = soup.select_one("a[class*='SongHeader']")
    artist = artist_tag.get_text(strip=True) if artist_tag else ""

    # If we couldn't get structured title/artist, try from <title> tag
    if not title or not artist:
        page_title = soup.title.get_text() if soup.title else ""
        # Genius format: "Artist – Song Title | Genius Lyrics"
        match = re.match(r"(.+?)\s*[–\-]\s*(.+?)\s*\|", page_title)
        if match:
            artist = artist or match.group(1).strip()
            title = title or match.group(2).strip().replace(" Lyrics", "")

    # Extract lyrics from data-lyrics-container divs
    containers = soup.select('div[data-lyrics-container="true"]')
    parts = []
    for c in containers:
        for br in c.find_all("br"):
            br.replace_with("\n")
        parts.append(c.get_text())

    raw_lyrics = "\n".join(parts).strip()

    # Parse with section awareness
    sections = []
    current_section = None
    current_lines = []
    all_lines = []  # For plain lyrics output

    for line in raw_lyrics.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Check if this is a section header
        if re.match(r"^\[.*\]$", line):
            # Save previous section if it has lines
            if current_lines:
                sections.append({
                    "section": current_section or "verse",
                    "lines": current_lines
                })
            # Start new section
            current_section = _normalize_section(line)
            current_lines = []
            continue

        # Skip junk lines
        if re.match(r"^\d+ Contributor", line):
            continue
        if line.endswith(" Lyrics"):
            continue
        if re.match(r'^[Vv]ersuri', line) or re.match(r'^\[Versuri', line):
            continue

        current_lines.append(line)
        all_lines.append(line)

    # Don't forget the last section
    if current_lines:
        sections.append({
            "section": current_section or "verse",
            "lines": current_lines
        })

    return {
        "title": title,
        "artist": artist,
        "lyrics": "\n".join(all_lines),
        "sections": sections,
    }
