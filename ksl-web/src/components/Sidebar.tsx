import { useState } from 'react';
import { api } from '../api';
import { useStore } from '../store';

export function Sidebar() {
  return (
    <div className="space-y-4">
      <RhymePanel />
      <CorpusPanel />
    </div>
  );
}

function RhymePanel() {
  const [word, setWord] = useState('');
  const [result, setResult] = useState<{
    perfect: string[];
    near: string[];
    slant: string[];
  } | null>(null);
  const { loading, setLoading } = useStore();

  const search = async () => {
    if (!word.trim()) return;
    setLoading('rhyme', true);
    try {
      const res = await api.rhymes(word.trim());
      setResult({ perfect: res.perfect, near: res.near, slant: res.slant });
    } finally {
      setLoading('rhyme', false);
    }
  };

  return (
    <div className="bg-zinc-900 rounded-xl p-4 border border-zinc-800">
      <h3 className="text-sm font-bold text-amber-400 mb-2">Rhymes</h3>
      <div className="flex gap-2 mb-3">
        <input
          value={word}
          onChange={(e) => setWord(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && search()}
          placeholder="Type a word..."
          className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1.5 text-sm flex-1"
        />
        <button
          onClick={search}
          disabled={loading['rhyme']}
          className="bg-amber-500 text-black px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-amber-400 disabled:opacity-50"
        >
          {loading['rhyme'] ? '...' : 'Find'}
        </button>
      </div>

      {result && (
        <div className="space-y-2 text-sm">
          {result.perfect.length > 0 && (
            <div>
              <span className="text-green-400 text-xs font-bold">PERFECT</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {result.perfect.map((w, i) => (
                  <span key={i} className="px-2 py-0.5 bg-green-500/10 text-green-300 rounded">{w}</span>
                ))}
              </div>
            </div>
          )}
          {result.near.length > 0 && (
            <div>
              <span className="text-yellow-400 text-xs font-bold">NEAR</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {result.near.map((w, i) => (
                  <span key={i} className="px-2 py-0.5 bg-yellow-500/10 text-yellow-300 rounded">{w}</span>
                ))}
              </div>
            </div>
          )}
          {result.slant.length > 0 && (
            <div>
              <span className="text-orange-400 text-xs font-bold">SLANT</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {result.slant.map((w, i) => (
                  <span key={i} className="px-2 py-0.5 bg-orange-500/10 text-orange-300 rounded">{w}</span>
                ))}
              </div>
            </div>
          )}
          {!result.perfect.length && !result.near.length && !result.slant.length && (
            <p className="text-zinc-500">No rhymes found. Try seeding the database first.</p>
          )}
        </div>
      )}
    </div>
  );
}

function CorpusPanel() {
  const [text, setText] = useState('');
  const [source, setSource] = useState('');
  const [url, setUrl] = useState('');
  const [status, setStatus] = useState('');
  const { loading, setLoading } = useStore();

  const ingest = async () => {
    if (!text.trim()) return;
    setLoading('ingest', true);
    try {
      const res = await api.corpusIngest(text.trim(), source || undefined);
      setStatus(`Added ${res.lines_added} lines, ${res.words_added} words to rhyme DB`);
      setText('');
    } finally {
      setLoading('ingest', false);
    }
  };

  const ingestFromUrl = async () => {
    if (!url.trim()) return;
    setLoading('ingestUrl', true);
    setStatus('');
    try {
      const res = await api.corpusIngestUrl(url.trim());
      setStatus(`${res.artist} - ${res.title}: ${res.lines_added} lines, ${res.words_added} words`);
      setUrl('');
    } catch (e: unknown) {
      setStatus(`Error: ${e instanceof Error ? e.message : 'Failed to scrape'}`);
    } finally {
      setLoading('ingestUrl', false);
    }
  };

  const importAsStyle = async () => {
    if (!text.trim()) return;
    setLoading('ingest', true);
    try {
      await api.styleImport(text.trim(), 'reference', source || undefined);
      setStatus('Imported as reference');
      setText('');
    } finally {
      setLoading('ingest', false);
    }
  };

  return (
    <div className="bg-zinc-900 rounded-xl p-4 border border-zinc-800">
      <h3 className="text-sm font-bold text-amber-400 mb-2">Import Lyrics</h3>

      <div className="flex gap-2 mb-3">
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && ingestFromUrl()}
          placeholder="Genius URL..."
          className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1.5 text-sm flex-1"
        />
        <button
          onClick={ingestFromUrl}
          disabled={loading['ingestUrl'] || !url.trim()}
          className="bg-purple-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-purple-500 disabled:opacity-50"
        >
          {loading['ingestUrl'] ? '...' : 'Scrape'}
        </button>
      </div>

      <div className="border-t border-zinc-800 pt-3">
        <input
          value={source}
          onChange={(e) => setSource(e.target.value)}
          placeholder="Artist name (optional)"
          className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1.5 text-sm w-full mb-2"
        />
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Or paste lyrics here..."
          rows={4}
          className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm w-full resize-none mb-2"
        />
        <div className="flex gap-2">
          <button
            onClick={ingest}
            disabled={loading['ingest'] || !text.trim()}
            className="bg-amber-500 text-black px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-amber-400 disabled:opacity-50 flex-1"
          >
            {loading['ingest'] ? '...' : 'Add to Corpus'}
          </button>
          <button
            onClick={importAsStyle}
            disabled={loading['ingest'] || !text.trim()}
            className="bg-zinc-700 text-zinc-300 px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-zinc-600 disabled:opacity-50 flex-1"
          >
            Import as Style
          </button>
        </div>
      </div>
      {status && <p className="text-xs text-green-400 mt-2">{status}</p>}
    </div>
  );
}
