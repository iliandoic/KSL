import { useState, useEffect } from 'react';
import { api } from '../api';
import { useStore } from '../store';

interface ScrapedSongSummary {
  id: number;
  title: string;
  artist: string;
  url: string;
  has_sonnet: boolean;
  has_opus: boolean;
  created_at: string;
}

interface ScrapedSongFull {
  id: number;
  title: string;
  artist: string;
  url: string;
  original_text: string;
  sections: { section: string; lines: string[] }[];
  sonnet_translations: Record<string, string>;
  opus_translations: Record<string, string>;
}

export function SongsPage() {
  const [songs, setSongs] = useState<ScrapedSongSummary[]>([]);
  const [selectedSong, setSelectedSong] = useState<ScrapedSongFull | null>(null);
  const [showTranslation, setShowTranslation] = useState<'sonnet' | 'opus' | null>('sonnet');
  const { loading, setLoading } = useStore();

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
          <p className="text-xs text-zinc-500 mt-1">{songs.length} songs</p>
        </div>

        {loading['songs'] ? (
          <div className="p-4 text-zinc-500">Loading...</div>
        ) : songs.length === 0 ? (
          <div className="p-4 text-zinc-500 text-sm">
            No songs yet. Go to Import to add some.
          </div>
        ) : (
          <div className="divide-y divide-zinc-800">
            {songs.map(song => (
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
              <div className="text-zinc-400">{selectedSong.artist}</div>
              <a
                href={selectedSong.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-teal-400 hover:underline"
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
