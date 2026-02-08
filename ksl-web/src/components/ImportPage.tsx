import { useState } from 'react';
import { api } from '../api';
import { useStore } from '../store';

type Section = { section: string; lines: string[] };

const SECTION_STYLES: Record<string, { label: string; bg: string; border: string; text: string }> = {
  hook: { label: 'Hook', bg: 'bg-amber-500/10', border: 'border-l-amber-500', text: 'text-amber-400' },
  'pre-hook': { label: 'Pre-Hook', bg: 'bg-purple-500/10', border: 'border-l-purple-500', text: 'text-purple-400' },
  'post-hook': { label: 'Post-Hook', bg: 'bg-pink-500/10', border: 'border-l-pink-500', text: 'text-pink-400' },
  verse: { label: 'Verse', bg: 'bg-blue-500/10', border: 'border-l-blue-500', text: 'text-blue-400' },
  bridge: { label: 'Bridge', bg: 'bg-green-500/10', border: 'border-l-green-500', text: 'text-green-400' },
  intro: { label: 'Intro', bg: 'bg-zinc-500/10', border: 'border-l-zinc-500', text: 'text-zinc-400' },
  outro: { label: 'Outro', bg: 'bg-zinc-500/10', border: 'border-l-zinc-500', text: 'text-zinc-400' },
};

function SectionView({ sections }: { sections: Section[] }) {
  // Deduplicate sections with identical content
  type DeduplicatedSection = { section: string; lines: string[]; count: number; positions: number[] };
  const deduped: DeduplicatedSection[] = [];
  const seenHashes = new Map<string, number>(); // hash -> index in deduped array

  sections.forEach((s, idx) => {
    // Create a hash from section type + lines content
    const hash = `${s.section}::${s.lines.join('\n')}`;

    if (seenHashes.has(hash)) {
      // Already seen this exact section, increment count
      const existingIdx = seenHashes.get(hash)!;
      deduped[existingIdx].count++;
      deduped[existingIdx].positions.push(idx + 1);
    } else {
      // New unique section
      seenHashes.set(hash, deduped.length);
      deduped.push({ ...s, count: 1, positions: [idx + 1] });
    }
  });

  // Count unique sections per type for numbering
  const typeCounts: Record<string, number> = {};
  deduped.forEach(s => {
    typeCounts[s.section] = (typeCounts[s.section] || 0) + 1;
  });

  // Track current number per type
  const currentNum: Record<string, number> = {};

  return (
    <div className="space-y-3 max-h-[400px] overflow-y-auto">
      {deduped.map((s, idx) => {
        const style = SECTION_STYLES[s.section] || SECTION_STYLES.verse;
        currentNum[s.section] = (currentNum[s.section] || 0) + 1;

        // Build label
        let label = style.label;
        if (typeCounts[s.section] > 1) {
          label = `${style.label} ${currentNum[s.section]}`;
        }

        // Add repeat indicator
        const repeatBadge = s.count > 1 ? (
          <span className="ml-2 px-1.5 py-0.5 bg-white/10 rounded text-[10px] font-medium">
            ×{s.count}
          </span>
        ) : null;

        return (
          <div
            key={idx}
            className={`${style.bg} border-l-4 ${style.border} rounded-r-lg overflow-hidden`}
          >
            <div className={`px-3 py-1.5 ${style.text} text-xs font-bold uppercase tracking-wide flex items-center`}>
              {label}
              {repeatBadge}
            </div>
            <div className="px-3 pb-3 space-y-0.5">
              {s.lines.map((line, lineIdx) => (
                <div key={lineIdx} className="text-sm text-zinc-200 font-mono">
                  {line}
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function ImportPage() {
  const [text, setText] = useState('');
  const [source, setSource] = useState('');
  const [url, setUrl] = useState('');
  const [status, setStatus] = useState('');
  const [sections, setSections] = useState<Section[]>([]);
  const [scrapedTitle, setScrapedTitle] = useState('');
  const [scrapedUrl, setScrapedUrl] = useState('');
  const [viewMode, setViewMode] = useState<'sections' | 'raw'>('sections');
  const { loading, setLoading } = useStore();

  const scrapeFromUrl = async () => {
    if (!url.trim()) return;
    setLoading('scrape', true);
    setStatus('');
    try {
      const res = await api.corpusScrapeUrl(url.trim());
      setText(res.lyrics);
      setSource(res.artist);
      setSections(res.sections);
      setScrapedTitle(res.title);
      setScrapedUrl(res.url);
      setViewMode('sections'); // Switch to section view after scraping

      // Count sections for status
      const sectionCounts = res.sections.reduce((acc, s) => {
        acc[s.section] = (acc[s.section] || 0) + s.lines.length;
        return acc;
      }, {} as Record<string, number>);

      const sectionSummary = Object.entries(sectionCounts)
        .map(([s, count]) => `${count} ${SECTION_STYLES[s]?.label || s}`)
        .join(', ');

      setStatus(`Scraped "${res.title}" by ${res.artist} - ${sectionSummary}`);
      setUrl('');
    } catch (e: unknown) {
      setStatus(`Error: ${e instanceof Error ? e.message : 'Failed to scrape'}`);
      setSections([]);
      setScrapedTitle('');
      setScrapedUrl('');
    } finally {
      setLoading('scrape', false);
    }
  };

  const ingest = async () => {
    if (!text.trim()) return;
    setLoading('ingest', true);
    try {
      const res = await api.corpusIngest(
        text.trim(),
        source || undefined,
        sections.length > 0 ? sections : undefined,
        scrapedTitle || undefined,
        scrapedUrl || undefined
      );

      const sectionSummary = Object.entries(res.sections_found || {})
        .map(([s, count]) => `${count} ${SECTION_STYLES[s]?.label || s}`)
        .join(', ');

      setStatus(`Added ${res.lines_added} lines, ${res.words_added} words${sectionSummary ? ` (${sectionSummary})` : ''}`);
      setText('');
      setSource('');
      setSections([]);
      setScrapedTitle('');
      setScrapedUrl('');
    } finally {
      setLoading('ingest', false);
    }
  };

  const importAsStyle = async () => {
    if (!text.trim()) return;
    setLoading('ingest', true);
    try {
      await api.styleImport(text.trim(), 'reference', source || undefined);
      setStatus('Imported as style reference');
      setText('');
    } finally {
      setLoading('ingest', false);
    }
  };

  const clearAll = () => {
    setText('');
    setSource('');
    setUrl('');
    setStatus('');
    setSections([]);
    setScrapedTitle('');
    setScrapedUrl('');
  };

  const hasSections = sections.length > 0;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
        <div className="border-b border-zinc-800 px-6 py-4">
          <h2 className="text-lg font-bold text-amber-400">Import Lyrics</h2>
          <p className="text-sm text-zinc-500 mt-1">
            Scrape from Genius or paste lyrics manually to add to your corpus
          </p>
        </div>

        <div className="p-6 space-y-6">
          {/* Genius URL Section */}
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
                className="bg-purple-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading['scrape'] ? 'Scraping...' : 'Scrape'}
              </button>
            </div>
          </div>

          {/* Artist Name + Song Title */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-2">
                Artist
              </label>
              <input
                value={source}
                onChange={(e) => setSource(e.target.value)}
                placeholder="Artist name"
                className="bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-sm w-full focus:border-amber-500 focus:outline-none"
              />
            </div>
            {scrapedTitle && (
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">
                  Song Title
                </label>
                <input
                  value={scrapedTitle}
                  onChange={(e) => setScrapedTitle(e.target.value)}
                  className="bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-sm w-full focus:border-amber-500 focus:outline-none"
                />
              </div>
            )}
          </div>

          {/* Lyrics Section */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-zinc-400">
                Lyrics
              </label>
              {hasSections && (
                <div className="flex gap-1 bg-zinc-800 rounded-lg p-0.5">
                  <button
                    onClick={() => setViewMode('sections')}
                    className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                      viewMode === 'sections'
                        ? 'bg-zinc-700 text-zinc-200'
                        : 'text-zinc-500 hover:text-zinc-300'
                    }`}
                  >
                    Sections
                  </button>
                  <button
                    onClick={() => setViewMode('raw')}
                    className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                      viewMode === 'raw'
                        ? 'bg-zinc-700 text-zinc-200'
                        : 'text-zinc-500 hover:text-zinc-300'
                    }`}
                  >
                    Raw
                  </button>
                </div>
              )}
            </div>

            {hasSections && viewMode === 'sections' ? (
              <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4">
                <SectionView sections={sections} />
              </div>
            ) : (
              <textarea
                value={text}
                onChange={(e) => {
                  setText(e.target.value);
                  // Clear sections and scraped metadata if user manually edits
                  if (sections.length > 0) {
                    setSections([]);
                    setScrapedTitle('');
                    setScrapedUrl('');
                  }
                }}
                placeholder="Paste or edit lyrics here..."
                rows={12}
                className="bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-sm w-full resize-none focus:border-amber-500 focus:outline-none font-mono"
              />
            )}
            <div className="flex justify-between mt-2 text-xs text-zinc-500">
              <span>{text.split('\n').filter(l => l.trim()).length} lines</span>
              <span>{text.length} characters</span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={ingest}
              disabled={loading['ingest'] || !text.trim()}
              className="bg-amber-500 text-black px-6 py-2.5 rounded-lg text-sm font-bold hover:bg-amber-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex-1"
            >
              {loading['ingest'] ? 'Adding...' : 'Add to Corpus'}
            </button>
            <button
              onClick={importAsStyle}
              disabled={loading['ingest'] || !text.trim()}
              className="bg-zinc-700 text-zinc-200 px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-zinc-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex-1"
            >
              Import as Style
            </button>
            <button
              onClick={clearAll}
              className="bg-zinc-800 text-zinc-400 px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-zinc-700 hover:text-zinc-200 transition-colors"
            >
              Clear
            </button>
          </div>

          {/* Status Message */}
          {status && (
            <div className={`text-sm px-4 py-3 rounded-lg ${
              status.startsWith('Error')
                ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                : 'bg-green-500/10 text-green-400 border border-green-500/20'
            }`}>
              {status}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
