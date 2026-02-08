import { useState } from 'react';
import { api } from '../api';
import { useStore } from '../store';

const THEMES = ['', 'money', 'love', 'enemies', 'party', 'street'];

export function SparkPanel() {
  const { sparkTab, setSparkTab, insertSuggestion, loading, setLoading } = useStore();

  return (
    <div className="bg-zinc-900 rounded-xl p-4 border border-zinc-800">
      <h2 className="text-lg font-bold mb-3 text-amber-400">Spark Generator</h2>
      <div className="flex gap-2 mb-4">
        {(['titles', 'random', 'explode'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setSparkTab(tab)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
              sparkTab === tab
                ? 'bg-amber-500 text-black'
                : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
            }`}
          >
            {tab === 'titles' ? 'Title First' : tab === 'random' ? 'Random Spark' : 'Word Explosion'}
          </button>
        ))}
      </div>

      {sparkTab === 'titles' && <TitleFirst />}
      {sparkTab === 'random' && <RandomSpark />}
      {sparkTab === 'explode' && <WordExplosion />}
    </div>
  );
}

function TitleFirst() {
  const [theme, setTheme] = useState('');
  const [titles, setTitles] = useState<string[]>([]);
  const [openingLines, setOpeningLines] = useState<string[]>([]);
  const [selectedTitle, setSelectedTitle] = useState('');
  const { insertSuggestion, loading, setLoading } = useStore();

  const generateTitles = async () => {
    setLoading('titles', true);
    try {
      const res = await api.sparkTitles(theme || undefined);
      setTitles(res.titles);
      setOpeningLines([]);
      setSelectedTitle('');
    } finally {
      setLoading('titles', false);
    }
  };

  const pickTitle = async (title: string) => {
    setSelectedTitle(title);
    setLoading('fromTitle', true);
    try {
      const res = await api.sparkFromTitle(title);
      setOpeningLines(res.opening_lines);
    } finally {
      setLoading('fromTitle', false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <select
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
          className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm flex-1"
        >
          <option value="">No theme</option>
          {THEMES.filter(Boolean).map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
        <button
          onClick={generateTitles}
          disabled={loading['titles']}
          className="bg-amber-500 text-black px-4 py-2 rounded-lg text-sm font-medium hover:bg-amber-400 disabled:opacity-50"
        >
          {loading['titles'] ? '...' : 'Generate Titles'}
        </button>
      </div>

      {titles.length > 0 && (
        <div className="space-y-1">
          {titles.map((t, i) => (
            <button
              key={i}
              onClick={() => pickTitle(t)}
              className={`block w-full text-left px-3 py-1.5 rounded text-sm transition ${
                selectedTitle === t ? 'bg-amber-500/20 text-amber-300' : 'hover:bg-zinc-800 text-zinc-300'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      )}

      {loading['fromTitle'] && <p className="text-zinc-500 text-sm">Generating lines...</p>}

      {openingLines.length > 0 && (
        <div className="border-t border-zinc-800 pt-3 space-y-1">
          <p className="text-xs text-zinc-500 mb-2">Click a line to add to editor:</p>
          {openingLines.map((line, i) => (
            <button
              key={i}
              onClick={() => insertSuggestion(line)}
              className="block w-full text-left px-3 py-1.5 rounded text-sm hover:bg-green-500/20 text-green-300 transition"
            >
              {line}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function RandomSpark() {
  const [spark, setSpark] = useState<{ spark: string; type: string } | null>(null);
  const { insertSuggestion, loading, setLoading } = useStore();

  const generate = async () => {
    setLoading('random', true);
    try {
      const res = await api.sparkRandom();
      setSpark(res);
    } finally {
      setLoading('random', false);
    }
  };

  return (
    <div className="space-y-3">
      <button
        onClick={generate}
        disabled={loading['random']}
        className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-4 rounded-xl text-lg font-bold hover:from-purple-500 hover:to-pink-500 disabled:opacity-50 transition"
      >
        {loading['random'] ? '...' : 'Random Spark'}
      </button>

      {spark && (
        <div
          onClick={() => insertSuggestion(spark.spark)}
          className="bg-zinc-800 rounded-lg p-4 cursor-pointer hover:bg-zinc-700 transition"
        >
          <span className="text-xs text-zinc-500 uppercase">{spark.type}</span>
          <p className="text-lg text-white mt-1">{spark.spark}</p>
        </div>
      )}
    </div>
  );
}

function WordExplosion() {
  const [word, setWord] = useState('');
  const [result, setResult] = useState<{
    starts_with: string[];
    ends_with: string[];
    rhymes: string[];
    combos: string[];
  } | null>(null);
  const { insertSuggestion, loading, setLoading } = useStore();

  const explode = async () => {
    if (!word.trim()) return;
    setLoading('explode', true);
    try {
      const res = await api.sparkExplode(word.trim());
      setResult(res);
    } finally {
      setLoading('explode', false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <input
          value={word}
          onChange={(e) => setWord(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && explode()}
          placeholder="Enter a word..."
          className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm flex-1"
        />
        <button
          onClick={explode}
          disabled={loading['explode'] || !word.trim()}
          className="bg-amber-500 text-black px-4 py-2 rounded-lg text-sm font-medium hover:bg-amber-400 disabled:opacity-50"
        >
          {loading['explode'] ? '...' : 'Explode'}
        </button>
      </div>

      {result && (
        <div className="space-y-3 text-sm">
          {([
            ['starts_with', 'Starts with', 'text-blue-300'],
            ['ends_with', 'Ends with', 'text-green-300'],
            ['rhymes', 'Rhymes', 'text-purple-300'],
            ['combos', 'Combos', 'text-pink-300'],
          ] as const).map(([key, label, color]) => {
            const items = result[key as keyof typeof result];
            if (!items?.length) return null;
            return (
              <div key={key}>
                <p className={`text-xs uppercase font-bold ${color} mb-1`}>{label}</p>
                <div className="flex flex-wrap gap-1">
                  {items.map((item, i) => (
                    <button
                      key={i}
                      onClick={() => insertSuggestion(item)}
                      className="px-2 py-1 bg-zinc-800 rounded hover:bg-zinc-700 transition text-zinc-300"
                    >
                      {item}
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
