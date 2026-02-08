import { useState, useEffect } from 'react';
import { api } from '../api';
import { useStore } from '../store';

interface FeaturedArtist {
  name: string;
  image: string;
}

interface ScrapedSongSummary {
  id: number;
  title: string;
  artist: string;
  url: string;
  primary_artist: string | null;
  primary_artist_image: string | null;
  featured_artists: FeaturedArtist[];
  has_sonnet: boolean;
  has_opus: boolean;
  created_at: string;
}

interface ScrapedSongFull {
  id: number;
  title: string;
  artist: string;
  url: string;
  primary_artist: string | null;
  primary_artist_image: string | null;
  featured_artists: FeaturedArtist[];
  original_text: string;
  sections: { section: string; lines: string[] }[];
  sonnet_translations: Record<string, string>;
  opus_translations: Record<string, string>;
}

export function SongsPage() {
  const [songs, setSongs] = useState<ScrapedSongSummary[]>([]);
  const [selectedSong, setSelectedSong] = useState<ScrapedSongFull | null>(null);
  const [showTranslation, setShowTranslation] = useState<'sonnet' | 'opus' | null>('sonnet');
  const [artistFilter, setArtistFilter] = useState<string>('');
  const { loading, setLoading } = useStore();

  // Get all artists from a song (primary + featured)
  const getSongArtists = (song: ScrapedSongSummary): string[] => {
    const artists: string[] = [];
    if (song.primary_artist) {
      artists.push(song.primary_artist);
    }
    if (song.featured_artists) {
      artists.push(...song.featured_artists.map(a => a.name));
    }
    // Fallback to legacy artist string parsing if no structured data
    if (artists.length === 0 && song.artist) {
      return song.artist
        .split(/\s*(?:&|,|\bfeat\.?\b|\bfeaturing\b|\bft\.?\b|\bx\b|\bX\b)\s*/i)
        .map(a => a.trim())
        .filter(a => a.length > 0);
    }
    return artists;
  };

  // Get unique individual artists for filter with images
  const artistMap = new Map<string, string | null>();
  songs.forEach(s => {
    if (s.primary_artist) {
      artistMap.set(s.primary_artist, s.primary_artist_image);
    }
    s.featured_artists?.forEach(fa => {
      if (!artistMap.has(fa.name)) {
        artistMap.set(fa.name, fa.image);
      }
    });
    // Fallback for legacy songs
    if (!s.primary_artist && s.artist) {
      getSongArtists(s).forEach(name => {
        if (!artistMap.has(name)) {
          artistMap.set(name, null);
        }
      });
    }
  });
  const artists = [...artistMap.keys()].sort();

  const filteredSongs = artistFilter
    ? songs.filter(s => getSongArtists(s).includes(artistFilter))
    : songs;

  useEffect(() => {
    loadSongs();
  }, []);

  const loadSongs = async () => {
    setLoading('songs', true);
    try {
      const res = await api.scrapedList();
      setSongs(res.songs);
    } catch (e) {
      console.error('Failed to load songs:', e);
    } finally {
      setLoading('songs', false);
    }
  };

  const selectSong = async (id: number) => {
    setLoading('song', true);
    try {
      const song = await api.scrapedGet(id);
      setSelectedSong(song);
    } catch (e) {
      console.error('Failed to load song:', e);
    } finally {
      setLoading('song', false);
    }
  };

  const deleteSong = async (id: number) => {
    if (!confirm('Delete this song?')) return;
    try {
      await api.scrapedDelete(id);
      setSongs(songs.filter(s => s.id !== id));
      if (selectedSong?.id === id) {
        setSelectedSong(null);
      }
    } catch (e) {
      console.error('Failed to delete song:', e);
    }
  };

  const getTranslation = (lineKey: string): string => {
    if (!selectedSong || !showTranslation) return '';
    const translations = showTranslation === 'sonnet'
      ? selectedSong.sonnet_translations
      : selectedSong.opus_translations;
    return translations?.[lineKey] || '';
  };

  return (
    <div className="flex h-full">
      {/* Song List */}
      <div className="w-80 border-r border-zinc-800 overflow-y-auto">
        <div className="p-4 border-b border-zinc-800">
          <h2 className="text-lg font-bold text-amber-400">Saved Songs</h2>
          <p className="text-xs text-zinc-500 mt-1">
            {artistFilter ? `${filteredSongs.length} of ${songs.length}` : songs.length} songs
          </p>
          {artists.length > 1 && (
            <div className="mt-2 space-y-1 max-h-48 overflow-y-auto">
              <button
                onClick={() => setArtistFilter('')}
                className={`w-full text-left px-2 py-1.5 rounded text-sm transition-colors ${
                  !artistFilter ? 'bg-amber-500/20 text-amber-400' : 'hover:bg-zinc-700 text-zinc-400'
                }`}
              >
                All Artists
              </button>
              {artists.map(artist => (
                <button
                  key={artist}
                  onClick={() => setArtistFilter(artist)}
                  className={`w-full text-left px-2 py-1.5 rounded text-sm transition-colors flex items-center gap-2 ${
                    artistFilter === artist ? 'bg-amber-500/20 text-amber-400' : 'hover:bg-zinc-700 text-zinc-300'
                  }`}
                >
                  {artistMap.get(artist) && (
                    <img
                      src={artistMap.get(artist)!}
                      alt={artist}
                      className="w-6 h-6 rounded-full object-cover"
                    />
                  )}
                  <span className="truncate">{artist}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {loading['songs'] ? (
          <div className="p-4 text-zinc-500">Loading...</div>
        ) : filteredSongs.length === 0 ? (
          <div className="p-4 text-zinc-500 text-sm">
            {songs.length === 0 ? 'No songs yet. Go to Import to add some.' : 'No songs match filter.'}
          </div>
        ) : (
          <div className="divide-y divide-zinc-800">
            {filteredSongs.map(song => (
              <div
                key={song.id}
                onClick={() => selectSong(song.id)}
                className={`p-3 cursor-pointer transition-colors ${
                  selectedSong?.id === song.id
                    ? 'bg-amber-500/10 border-l-2 border-amber-500'
                    : 'hover:bg-zinc-800/50'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm truncate">{song.title}</div>
                    <div className="text-xs text-zinc-500 truncate">{song.artist}</div>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteSong(song.id); }}
                    className="text-zinc-600 hover:text-red-400 p-1"
                    title="Delete"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
                <div className="flex gap-1 mt-1">
                  {song.has_sonnet && (
                    <span className="text-[10px] px-1.5 py-0.5 bg-purple-500/20 text-purple-400 rounded">Sonnet</span>
                  )}
                  {song.has_opus && (
                    <span className="text-[10px] px-1.5 py-0.5 bg-amber-500/20 text-amber-400 rounded">Opus</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Song Detail */}
      <div className="flex-1 overflow-y-auto">
        {loading['song'] ? (
          <div className="p-8 text-zinc-500">Loading...</div>
        ) : !selectedSong ? (
          <div className="p-8 text-zinc-500 text-center">
            <div className="text-4xl mb-2">Select a song</div>
            <div className="text-sm">Click on a song to view lyrics and translations</div>
          </div>
        ) : (
          <div className="p-6">
            {/* Header */}
            <div className="mb-6">
              <h2 className="text-2xl font-bold">{selectedSong.title}</h2>
              <div className="flex items-center gap-3 mt-2">
                {selectedSong.primary_artist_image && (
                  <img
                    src={selectedSong.primary_artist_image}
                    alt={selectedSong.primary_artist || ''}
                    className="w-10 h-10 rounded-full object-cover"
                  />
                )}
                <div>
                  <div className="text-zinc-300">
                    {selectedSong.primary_artist || selectedSong.artist}
                  </div>
                  {selectedSong.featured_artists?.length > 0 && (
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-zinc-500">feat.</span>
                      {selectedSong.featured_artists.map((fa, i) => (
                        <div key={i} className="flex items-center gap-1">
                          {fa.image && (
                            <img src={fa.image} alt={fa.name} className="w-5 h-5 rounded-full object-cover" />
                          )}
                          <span className="text-xs text-zinc-400">{fa.name}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <a
                href={selectedSong.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-teal-400 hover:underline mt-2 inline-block"
              >
                View on Genius
              </a>
            </div>

            {/* Translation Toggle */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setShowTranslation(null)}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  showTranslation === null
                    ? 'bg-zinc-700 text-white'
                    : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'
                }`}
              >
                Original Only
              </button>
              <button
                onClick={() => setShowTranslation('sonnet')}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  showTranslation === 'sonnet'
                    ? 'bg-purple-600 text-white'
                    : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'
                }`}
              >
                + Sonnet
              </button>
              <button
                onClick={() => setShowTranslation('opus')}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  showTranslation === 'opus'
                    ? 'bg-amber-500 text-black'
                    : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'
                }`}
              >
                + Opus
              </button>
            </div>

            {/* Lyrics */}
            <div className="space-y-6">
              {selectedSong.sections.map((section, sIdx) => (
                <div key={sIdx} className="bg-zinc-800/30 rounded-lg p-4">
                  <div className="text-xs text-teal-400 font-medium mb-3 uppercase">
                    [{section.section}]
                  </div>
                  <div className="space-y-2">
                    {section.lines.map((line, lIdx) => {
                      const lineKey = `${sIdx}-${lIdx}`;
                      const translation = getTranslation(lineKey);
                      return (
                        <div key={lIdx} className="group">
                          <div className="text-zinc-200">{line}</div>
                          {showTranslation && translation && (
                            <div className={`text-sm mt-0.5 ${
                              showTranslation === 'sonnet' ? 'text-purple-400' : 'text-amber-400'
                            }`}>
                              {translation}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
