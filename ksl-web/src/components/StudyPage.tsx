import { useState, useEffect } from 'react';
import { api } from '../api';

interface Artist {
  artist: string;
  songs_studied: number;
}

interface RhymeGroup {
  group_name: string;
  endings: string[];
  example_words: Record<string, string[]>;
  frequency: number;
}

interface ArtistStudy {
  artist: string;
  songs_studied: number;
  vocabulary: Record<string, number>;
  concepts: string[];
  prompts: string[];
  titles: string[];
  rhyme_groups: RhymeGroup[];
}

export function StudyPage() {
  const [artists, setArtists] = useState<Artist[]>([]);
  const [selectedArtist, setSelectedArtist] = useState<string | null>(null);
  const [study, setStudy] = useState<ArtistStudy | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedSection, setExpandedSection] = useState<string | null>('vocabulary');

  useEffect(() => {
    loadArtists();
  }, []);

  const loadArtists = async () => {
    try {
      const res = await api.studyArtists();
      setArtists(res.artists);
      if (res.artists.length === 1) {
        selectArtist(res.artists[0].artist);
      }
    } catch (e) {
      console.error('Failed to load artists:', e);
    }
  };

  const selectArtist = async (artist: string) => {
    setSelectedArtist(artist);
    setLoading(true);
    try {
      const res = await api.studyArtist(artist);
      setStudy(res);
    } catch (e) {
      console.error('Failed to load artist study:', e);
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  if (artists.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 p-8 text-center">
        <div className="text-6xl">📚</div>
        <h2 className="text-2xl font-bold text-white">No artists studied yet!</h2>
        <p className="text-zinc-400 max-w-md">
          Go to the Import page, search for an artist, and scrape some songs to start building your inspiration pool.
        </p>
        <button
          onClick={() => window.location.hash = '#import'}
          className="mt-4 px-6 py-3 bg-amber-500 text-black font-bold rounded-lg hover:bg-amber-400"
        >
          Go to Import
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4">
      {/* Artist Selector */}
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4 mb-4">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-zinc-400">Artist:</label>
          <select
            value={selectedArtist || ''}
            onChange={(e) => e.target.value && selectArtist(e.target.value)}
            className="bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2 text-sm text-zinc-200 flex-1 focus:border-amber-500 focus:outline-none"
          >
            <option value="">Select an artist...</option>
            {artists.map((a) => (
              <option key={a.artist} value={a.artist}>
                {a.artist} ({a.songs_studied} songs)
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-zinc-400">Loading...</div>
        </div>
      )}

      {study && !loading && (
        <div className="space-y-4">
          {/* Header Stats */}
          <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
            <h2 className="text-xl font-bold text-amber-400 mb-2">{study.artist}</h2>
            <div className="flex gap-6 text-sm text-zinc-400">
              <span>{study.songs_studied} songs studied</span>
              <span>{Object.keys(study.vocabulary).length} vocabulary words</span>
              <span>{study.concepts.length} concepts</span>
              <span>{study.prompts.length} prompts</span>
              <span>{study.rhyme_groups.length} rhyme groups</span>
            </div>
          </div>

          {/* Vocabulary Section */}
          <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
            <button
              onClick={() => toggleSection('vocabulary')}
              className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-zinc-800 transition-colors"
            >
              <div className="flex items-center gap-2">
                <span>📖</span>
                <span className="font-medium text-white">Vocabulary</span>
                <span className="text-zinc-500 text-sm">({Object.keys(study.vocabulary).length})</span>
              </div>
              <span className="text-zinc-500">{expandedSection === 'vocabulary' ? '−' : '+'}</span>
            </button>
            {expandedSection === 'vocabulary' && (
              <div className="px-4 pb-4">
                <div className="flex flex-wrap gap-2 max-h-64 overflow-y-auto">
                  {Object.entries(study.vocabulary)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 100)
                    .map(([word, count]) => (
                      <span
                        key={word}
                        className="px-2 py-1 bg-zinc-800 rounded text-sm text-zinc-300"
                        title={`Used ${count} times`}
                      >
                        {word}
                        <span className="text-zinc-500 ml-1 text-xs">{count}</span>
                      </span>
                    ))}
                </div>
              </div>
            )}
          </div>

          {/* Concepts Section */}
          <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
            <button
              onClick={() => toggleSection('concepts')}
              className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-zinc-800 transition-colors"
            >
              <div className="flex items-center gap-2">
                <span>💡</span>
                <span className="font-medium text-white">Concepts</span>
                <span className="text-zinc-500 text-sm">({study.concepts.length})</span>
              </div>
              <span className="text-zinc-500">{expandedSection === 'concepts' ? '−' : '+'}</span>
            </button>
            {expandedSection === 'concepts' && (
              <div className="px-4 pb-4">
                <div className="space-y-2">
                  {study.concepts.map((concept, i) => (
                    <div key={i} className="px-3 py-2 bg-zinc-800 rounded text-zinc-200">
                      {concept}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Prompts Section */}
          <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
            <button
              onClick={() => toggleSection('prompts')}
              className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-zinc-800 transition-colors"
            >
              <div className="flex items-center gap-2">
                <span>❓</span>
                <span className="font-medium text-white">Prompts</span>
                <span className="text-zinc-500 text-sm">({study.prompts.length})</span>
              </div>
              <span className="text-zinc-500">{expandedSection === 'prompts' ? '−' : '+'}</span>
            </button>
            {expandedSection === 'prompts' && (
              <div className="px-4 pb-4">
                <div className="space-y-2">
                  {study.prompts.map((prompt, i) => (
                    <div key={i} className="px-3 py-2 bg-zinc-800 rounded text-zinc-200 italic">
                      {prompt}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Titles Section */}
          <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
            <button
              onClick={() => toggleSection('titles')}
              className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-zinc-800 transition-colors"
            >
              <div className="flex items-center gap-2">
                <span>🎵</span>
                <span className="font-medium text-white">Titles</span>
                <span className="text-zinc-500 text-sm">({study.titles.length})</span>
              </div>
              <span className="text-zinc-500">{expandedSection === 'titles' ? '−' : '+'}</span>
            </button>
            {expandedSection === 'titles' && (
              <div className="px-4 pb-4">
                <div className="flex flex-wrap gap-2">
                  {study.titles.map((title, i) => (
                    <span key={i} className="px-3 py-1.5 bg-zinc-800 rounded text-zinc-200">
                      {title}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Rhyme Groups Section */}
          <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
            <button
              onClick={() => toggleSection('rhymes')}
              className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-zinc-800 transition-colors"
            >
              <div className="flex items-center gap-2">
                <span>🔤</span>
                <span className="font-medium text-white">Rhyme Groups</span>
                <span className="text-zinc-500 text-sm">({study.rhyme_groups.length})</span>
              </div>
              <span className="text-zinc-500">{expandedSection === 'rhymes' ? '−' : '+'}</span>
            </button>
            {expandedSection === 'rhymes' && (
              <div className="px-4 pb-4">
                <div className="space-y-3">
                  {study.rhyme_groups
                    .sort((a, b) => b.frequency - a.frequency)
                    .map((group, i) => (
                      <div key={i} className="bg-zinc-800 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="px-2 py-0.5 bg-amber-500/20 text-amber-400 rounded font-mono text-sm font-bold">
                            {group.group_name}
                          </span>
                          <span className="text-zinc-500 text-xs">
                            {group.frequency} occurrences
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {group.endings.map((ending, j) => (
                            <span
                              key={j}
                              className="px-2 py-1 bg-zinc-700 rounded font-mono text-sm text-zinc-300"
                            >
                              {ending}
                            </span>
                          ))}
                        </div>
                        {Object.keys(group.example_words).length > 0 && (
                          <div className="mt-2 text-xs text-zinc-500">
                            Examples:{' '}
                            {Object.entries(group.example_words)
                              .flatMap(([_, words]) => words)
                              .slice(0, 5)
                              .join(', ')}
                          </div>
                        )}
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
