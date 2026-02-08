"""Genius API client for artist/song discovery."""
import requests
from config import settings


BASE_URL = "https://api.genius.com"


def _headers():
    return {"Authorization": f"Bearer {settings.GENIUS_ACCESS_TOKEN}"}


def search_artists(query: str, limit: int = 10) -> list[dict]:
    """Search for artists by name."""
    response = requests.get(
        f"{BASE_URL}/search",
        params={"q": query},
        headers=_headers()
    )
    response.raise_for_status()

    hits = response.json().get("response", {}).get("hits", [])

    # Extract unique artists
    artists = {}
    for hit in hits:
        result = hit.get("result", {})
        artist = result.get("primary_artist", {})
        artist_id = artist.get("id")
        if artist_id and artist_id not in artists:
            artists[artist_id] = {
                "id": artist_id,
                "name": artist.get("name"),
                "image_url": artist.get("image_url"),
            }

    return list(artists.values())[:limit]


def get_artist_songs(artist_id: int, limit: int = 50) -> list[dict]:
    """Get songs by an artist."""
    songs = []
    page = 1
    per_page = 50

    while len(songs) < limit:
        response = requests.get(
            f"{BASE_URL}/artists/{artist_id}/songs",
            params={"page": page, "per_page": per_page, "sort": "popularity"},
            headers=_headers()
        )
        response.raise_for_status()

        data = response.json().get("response", {})
        page_songs = data.get("songs", [])

        if not page_songs:
            break

        for song in page_songs:
            songs.append({
                "id": song.get("id"),
                "title": song.get("title"),
                "url": song.get("url"),
                "primary_artist": song.get("primary_artist", {}).get("name"),
                "release_date": song.get("release_date_for_display"),
            })

        page += 1
        if len(page_songs) < per_page:
            break

    return songs[:limit]


def get_song_details(song_id: int) -> dict:
    """Get detailed info about a song."""
    response = requests.get(
        f"{BASE_URL}/songs/{song_id}",
        headers=_headers()
    )
    response.raise_for_status()

    song = response.json().get("response", {}).get("song", {})
    primary = song.get("primary_artist", {})
    return {
        "id": song.get("id"),
        "title": song.get("title"),
        "url": song.get("url"),
        "primary_artist": primary.get("name"),
        "primary_artist_image": primary.get("image_url"),
        "featured_artists": [
            {"name": a.get("name"), "image": a.get("image_url")}
            for a in song.get("featured_artists", [])
        ],
        "release_date": song.get("release_date_for_display"),
        "description": song.get("description", {}).get("plain") if song.get("description") else None,
    }


def get_song_id_from_url(url: str) -> int | None:
    """Extract song ID from Genius URL by fetching the page."""
    import re
    # Try to get song ID from the API by searching for the URL
    # Genius URLs don't contain the ID directly, so we need to search
    try:
        # Extract the slug from URL
        match = re.search(r'genius\.com/(.+?)(?:-lyrics)?/?$', url)
        if not match:
            return None
        slug = match.group(1)

        # Search for the song
        response = requests.get(
            f"{BASE_URL}/search",
            params={"q": slug.replace("-", " ")},
            headers=_headers()
        )
        response.raise_for_status()

        hits = response.json().get("response", {}).get("hits", [])
        for hit in hits:
            result = hit.get("result", {})
            if result.get("url", "").rstrip("/") == url.rstrip("/"):
                return result.get("id")

        # If exact match not found, return first result
        if hits:
            return hits[0].get("result", {}).get("id")
    except Exception:
        pass
    return None
