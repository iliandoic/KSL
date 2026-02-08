"""
Genius lyrics scraper. Fetches lyrics from a Genius URL.
"""
import re
import time
import random
import requests

from bs4 import BeautifulSoup

# Rotate user agents to avoid detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

def _get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    }

# Session for persistent cookies
_session = requests.Session()

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


def scrape_genius(url: str, retry_count: int = 2) -> dict:
    """
    Scrape lyrics from a Genius URL.
    Returns {"title": str, "artist": str, "lyrics": str, "sections": list}

    sections is a list of {"section": str, "lines": list[str]}
    """
    # Small random delay to avoid rate limiting
    time.sleep(random.uniform(0.5, 1.5))

    last_error = None
    for attempt in range(retry_count + 1):
        try:
            resp = _session.get(url, headers=_get_headers(), timeout=20)
            resp.raise_for_status()
            html = resp.text
            break
        except requests.exceptions.HTTPError as e:
            last_error = e
            if e.response.status_code == 403 and attempt < retry_count:
                # Wait longer and retry
                time.sleep(random.uniform(2, 4))
                continue
            raise
    else:
        raise last_error

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
