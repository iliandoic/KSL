import { useState } from 'react';
import { api } from '../api';
import { useStore } from '../store';

interface StudyResult {
  song_id: number;
  title: string;
  artist: string;
  language: string;
  lines_translated: number;
  study: {
    artist: string;
    title: string;
    endings_added: number;
    vocabulary_added: number;
    concepts_added: number;
    prompts_added: number;
  };
}

interface ArtistSong {
  id: number;
  title: string;
  url: string;
  imported: boolean;
}

export function ImportPage() {
  const [url, setUrl] = useState('');
  const [artistQuery, setArtistQuery] = useState('');
  const [artists, setArtists] = useState<{ id: number; name: string }[]>([]);
  const [selectedArtist, setSelectedArtist] = useState<{ id: number; name: string } | null>(null);
  const [artistSongs, setArtistSongs] = useState<ArtistSong[]>([]);
  const [selectedSongIds, setSelectedSongIds] = useState<Set<number>>(new Set());
  const [status, setStatus] = useState('');
  const [results, setResults] = useState<StudyResult[]>([]);
  const [progress, setProgress] = useState<{ current: number; total: number } | null>(null);
  const [aiModel, setAiModel] = useState<'sonnet' | 'opus'>('sonnet');
  const [showImported, setShowImported] = useState(false);
  const { loading, setLoading } = useStore();

  const notImportedSongs = artistSongs.filter(s => !s.imported);
  const importedSongs = artistSongs.filter(s => s.imported);

  const searchArtists = async () => {
    if (!artistQuery.trim()) return;
    setLoading('artist', true);
    try {
      const res = await api.geniusSearchArtists(artistQuery.trim());
      setArtists(res.artists);
      if (res.artists.length === 1) {
        selectArtist(res.artists[0]);
      }
    } catch (e: unknown) {
      setStatus(`Error: ${e instanceof Error ? e.message : 'Search failed'}`);
    } finally {
      setLoading('artist', false);
    }
  };

  const selectArtist = async (artist: { id: number; name: string }) => {
    setSelectedArtist(artist);
    setArtists([]);
    setLoading('songs', true);
    try {
      const res = await api.geniusArtistSongs(artist.id, 100);
      setArtistSongs(res.songs);
    } catch (e: unknown) {
      setStatus(`Error: ${e instanceof Error ? e.message : 'Failed to load songs'}`);
    } finally {
      setLoading('songs', false);
    }
  };

  const toggleSongSelection = (id: number) => {
    setSelectedSongIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const selectAllSongs = () => {
    setSelectedSongIds(new Set(notImportedSongs.map(s => s.id)));
  };

  const deselectAllSongs = () => {
    setSelectedSongIds(new Set());
  };

  const scrapeAndStudySelected = async () => {
    const songsToProcess = artistSongs.filter(s => selectedSongIds.has(s.id));
    if (songsToProcess.length === 0) return;

    setLoading('batch', true);
    setResults([]);
    setProgress({ current: 0, total: songsToProcess.length });

    const newResults: StudyResult[] = [];
    for (let i = 0; i < songsToProcess.length; i++) {
      const song = songsToProcess[i];
      setStatus(`Processing ${i + 1}/${songsToProcess.length}: "${song.title}"...`);
      setProgress({ current: i + 1, total: songsToProcess.length });

      try {
        const result = await api.scrapeAndStudy(song.url, aiModel);
        newResults.push(result);
        setResults([...newResults]);
      } catch (e) {
        console.error(`Failed to process ${song.title}:`, e);
      }
    }

    setProgress(null);
    setSelectedSongIds(new Set());
    setStatus(`Completed! Processed ${newResults.length} songs.`);

    // Refresh the songs list to update imported status
    if (selectedArtist) {
      try {
        const res = await api.geniusArtistSongs(selectedArtist.id, 100);
        setArtistSongs(res.songs);
      } catch {
        // If refresh fails, just clear the list
        setArtistSongs([]);
        setSelectedArtist(null);
      }
    }
    setLoading('batch', false);
  };

  const scrapeFromUrl = async () => {
    if (!url.trim()) return;
    setLoading('scrape', true);
    setStatus('Processing...');
    setResults([]);

    try {
      const result = await api.scrapeAndStudy(url.trim(), aiModel);
      setResults([result]);
      setStatus(`Added "${result.title}" by ${result.artist} to your inspiration pool!`);
      setUrl('');
    } catch (e: unknown) {
      setStatus(`Error: ${e instanceof Error ? e.message : 'Failed to process'}`);
    } finally {
      setLoading('scrape', false);
    }
  };

  const clearAll = () => {
    setUrl('');
    setArtistQuery('');
    setArtists([]);
    setSelectedArtist(null);
    setArtistSongs([]);
    setSelectedSongIds(new Set());
    setStatus('');
    setResults([]);
    setProgress(null);
  };

  return (
    <div className="max-w-3xl mx-auto p-4">
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
        <div className="border-b border-zinc-800 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-amber-400">Import Songs</h2>
              <p className="text-sm text-zinc-500 mt-1">
                Search for an artist or paste a Genius URL to add songs to your inspiration pool
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-zinc-500">Model:</span>
              <div className="flex gap-1 bg-zinc-800 rounded-lg p-0.5">
                <button
                  onClick={() => setAiModel('sonnet')}
                  className={`px-2 py-1 text-xs font-medium rounded transition-colors ${
                    aiModel === 'sonnet'
                      ? 'bg-purple-600 text-white'
                      : 'text-zinc-500 hover:text-zinc-300'
                  }`}
                >
                  Sonnet
                </button>
                <button
                  onClick={() => setAiModel('opus')}
                  className={`px-2 py-1 text-xs font-medium rounded transition-colors ${
                    aiModel === 'opus'
                      ? 'bg-amber-500 text-black'
                      : 'text-zinc-500 hover:text-zinc-300'
                  }`}
                >
                  Opus
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Artist Search */}
          <div>
            <label className="block text-sm font-medium text-zinc-400 mb-2">
              Find Artist
            </label>
            <div className="flex gap-3">
              <input
                value={artistQuery}
                onChange={(e) => setArtistQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && searchArtists()}
                placeholder="Search artist name..."
                className="bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-sm flex-1 focus:border-teal-500 focus:outline-none"
              />
              <button
                onClick={searchArtists}
                disabled={loading['artist'] || !artistQuery.trim()}
                className="bg-teal-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-teal-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading['artist'] ? '...' : 'Search'}
              </button>
            </div>

            {/* Artist Results */}
            {artists.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {artists.map(a => (
                  <button
                    key={a.id}
                    onClick={() => selectArtist(a)}
                    className="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm hover:border-teal-500 transition-colors"
                  >
                    {a.name}
                  </button>
                ))}
              </div>
            )}

            {/* Artist Songs */}
            {selectedArtist && artistSongs.length > 0 && (
              <div className="mt-4 bg-zinc-800/50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-teal-400 font-medium">
                    {selectedArtist.name} ({notImportedSongs.length} new, {importedSongs.length} imported)
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={selectedSongIds.size === notImportedSongs.length ? deselectAllSongs : selectAllSongs}
                      className="px-2 py-1 text-xs text-zinc-400 hover:text-zinc-200"
                    >
                      {selectedSongIds.size === notImportedSongs.length ? 'Deselect All' : 'Select All New'}
                    </button>
                    <button
                      onClick={() => { setSelectedArtist(null); setArtistSongs([]); setSelectedSongIds(new Set()); }}
                      className="text-xs text-zinc-500 hover:text-zinc-300"
                    >
                      Clear
                    </button>
                  </div>
                </div>

                {/* Not Imported Songs */}
                {notImportedSongs.length > 0 && (
                  <div className="max-h-48 overflow-y-auto space-y-1 mb-4">
                    {notImportedSongs.map(song => (
                      <div
                        key={song.id}
                        onClick={() => toggleSongSelection(song.id)}
                        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm cursor-pointer transition-colors ${
                          selectedSongIds.has(song.id)
                            ? 'bg-teal-500/20 border border-teal-500'
                            : 'bg-zinc-800 border border-zinc-700 hover:border-zinc-600'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedSongIds.has(song.id)}
                          onChange={() => {}}
                          className="accent-teal-500"
                        />
                        <span className="flex-1">{song.title}</span>
                      </div>
                    ))}
                  </div>
                )}

                {notImportedSongs.length === 0 && (
                  <div className="text-sm text-zinc-500 mb-4 py-4 text-center">
                    All songs from this artist are already imported
                  </div>
                )}

                {/* Already Imported Songs (Collapsible) */}
                {importedSongs.length > 0 && (
                  <div className="mb-4">
                    <button
                      onClick={() => setShowImported(!showImported)}
                      className="flex items-center gap-2 text-xs text-zinc-500 hover:text-zinc-300 mb-2"
                    >
                      <span>{showImported ? '▼' : '▶'}</span>
                      <span>Already imported ({importedSongs.length})</span>
                    </button>
                    {showImported && (
                      <div className="max-h-32 overflow-y-auto space-y-1 pl-4">
                        {importedSongs.map(song => (
                          <div
                            key={song.id}
                            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm bg-zinc-800/50 border border-zinc-700/50 text-zinc-500"
                          >
                            <span className="text-green-500">✓</span>
                            <span className="flex-1">{song.title}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {selectedSongIds.size > 0 && (
                  <button
                    onClick={scrapeAndStudySelected}
                    disabled={loading['batch']}
                    className="w-full py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-black font-bold rounded-lg hover:from-amber-400 hover:to-orange-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  >
                    {loading['batch']
                      ? `Processing... (${progress?.current}/${progress?.total})`
                      : `Scrape & Study ${selectedSongIds.size} songs`}
                  </button>
                )}
              </div>
            )}
            {loading['songs'] && <div className="mt-3 text-sm text-zinc-500">Loading songs...</div>}
          </div>

          {/* Divider */}
          <div className="flex items-center gap-4">
            <div className="flex-1 h-px bg-zinc-800"></div>
            <span className="text-zinc-500 text-sm">or</span>
            <div className="flex-1 h-px bg-zinc-800"></div>
          </div>

          {/* URL Input */}
          <div>
            <label className="block text-sm font-medium text-zinc-400 mb-2">
              Genius URL
            </label>
            <div className="flex gap-3">
              <input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && scrapeFromUrl()}
                placeholder="https://genius.com/..."
                className="bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-sm flex-1 focus:border-purple-500 focus:outline-none"
              />
              <button
                onClick={scrapeFromUrl}
                disabled={loading['scrape'] || !url.trim()}
                className="bg-gradient-to-r from-amber-500 to-orange-500 text-black px-6 py-2.5 rounded-lg text-sm font-bold hover:from-amber-400 hover:to-orange-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {loading['scrape'] ? 'Processing...' : 'Scrape & Study'}
              </button>
            </div>
          </div>

          {/* Results */}
          {results.length > 0 && (
            <div className="space-y-2">
              <div className="text-sm font-medium text-zinc-400">Results:</div>
              {results.map((r, i) => (
                <div key={i} className="bg-zinc-800/50 rounded-lg p-3 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-white font-medium">{r.artist} - {r.title}</span>
                    <span className="text-zinc-500 text-xs">{r.language === 'bg' ? 'Bulgarian' : 'Translated'}</span>
                  </div>
                  <div className="mt-1 text-zinc-500 text-xs">
                    +{r.study.vocabulary_added} words, +{r.study.concepts_added} concepts, +{r.study.prompts_added} prompts, +{r.study.endings_added} endings
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Status */}
          {status && (
            <div className={`text-sm px-4 py-3 rounded-lg ${
              status.startsWith('Error')
                ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                : 'bg-green-500/10 text-green-400 border border-green-500/20'
            }`}>
              {status}
            </div>
          )}

          {/* Clear Button */}
          {(results.length > 0 || status) && (
            <button
              onClick={clearAll}
              className="w-full py-2 bg-zinc-800 text-zinc-400 rounded-lg text-sm font-medium hover:bg-zinc-700 hover:text-zinc-200 transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
