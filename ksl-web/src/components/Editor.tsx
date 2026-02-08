import { useCallback, useEffect } from 'react';
import { api } from '../api';
import { useStore } from '../store';

const THEMES = ['', 'money', 'love', 'enemies', 'party', 'street'];

export function Editor() {
  const {
    lines, theme, suggestions,
    setLine, setSyllables, addLine, removeLine,
    setTheme, setSuggestions, insertSuggestion,
    loading, setLoading,
  } = useStore();

  const countSyllables = useCallback(async (index: number, text: string) => {
    if (!text.trim()) {
      setSyllables(index, 0);
      return;
    }
    try {
      const res = await api.syllables(text);
      setSyllables(index, res.count);
    } catch { /* ignore */ }
  }, [setSyllables]);

  const handleLineChange = (index: number, text: string) => {
    setLine(index, text);
    // Debounced syllable count
    const timer = setTimeout(() => countSyllables(index, text), 300);
    return () => clearTimeout(timer);
  };

  const handleComplete = async () => {
    const nonEmpty = lines.filter((l) => l.text.trim()).map((l) => l.text);
    if (!nonEmpty.length) return;
    setLoading('complete', true);
    try {
      const res = await api.complete(nonEmpty, theme || undefined);
      setSuggestions(res.suggestions);
    } finally {
      setLoading('complete', false);
    }
  };

  return (
    <div className="bg-zinc-900 rounded-xl p-4 border border-zinc-800">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-bold text-amber-400">Editor</h2>
        <select
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
          className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1.5 text-sm"
        >
          <option value="">No theme</option>
          {THEMES.filter(Boolean).map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      <div className="space-y-2 mb-4">
        {lines.map((line, i) => (
          <div key={i} className="flex items-center gap-2">
            <span className="text-xs text-zinc-600 w-6 text-right">{i + 1}</span>
            <input
              value={line.text}
              onChange={(e) => handleLineChange(i, e.target.value)}
              placeholder="Write a line..."
              className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm flex-1 focus:border-amber-500 focus:outline-none"
            />
            <span className="text-xs text-zinc-500 w-8 text-center font-mono">
              {line.syllables !== null && line.syllables > 0 ? line.syllables : ''}
            </span>
            {lines.length > 1 && (
              <button
                onClick={() => removeLine(i)}
                className="text-zinc-600 hover:text-red-400 text-sm"
              >
                x
              </button>
            )}
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <button
          onClick={addLine}
          className="text-sm text-zinc-500 hover:text-zinc-300 px-3 py-1.5"
        >
          + Add line
        </button>
        <button
          onClick={handleComplete}
          disabled={loading['complete']}
          className="bg-amber-500 text-black px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-amber-400 disabled:opacity-50 ml-auto"
        >
          {loading['complete'] ? 'Thinking...' : 'Complete next line'}
        </button>
      </div>

      {suggestions.length > 0 && (
        <div className="mt-3 border-t border-zinc-800 pt-3 space-y-1">
          <p className="text-xs text-zinc-500 mb-2">Suggestions (click to insert):</p>
          {suggestions.map((s, i) => (
            <button
              key={i}
              onClick={() => insertSuggestion(s)}
              className="block w-full text-left px-3 py-1.5 rounded text-sm hover:bg-green-500/20 text-green-300 transition"
            >
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
