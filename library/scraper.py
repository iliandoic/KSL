"""
Genius lyrics scraper. Fetches lyrics from a Genius URL.
"""
import re
import urllib.request

from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def scrape_genius(url: str) -> dict:
    """
    Scrape lyrics from a Genius URL.
    Returns {"title": str, "artist": str, "lyrics": str}
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

    # Clean up: remove section headers like [Refren], [Verse 1], etc.
    lines = []
    for line in raw_lyrics.split("\n"):
        line = line.strip()
        if not line:
            continue
        if re.match(r"^\[.*\]$", line):
            continue  # Skip section headers
        if re.match(r"^\d+ Contributor", line):
            continue  # Skip "2 Contributors" etc.
        if line.endswith(" Lyrics"):
            continue  # Skip title line like "CĂȚEL Lyrics"
        # Skip lines that are just the song title/section label
        if re.match(r'^[Vv]ersuri', line) or re.match(r'^\[Versuri', line):
            continue
        lines.append(line)

    lyrics = "\n".join(lines)

    return {
        "title": title,
        "artist": artist,
        "lyrics": lyrics,
    }
