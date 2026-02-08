import { useState, useEffect, useCallback } from 'react';
import { api } from '../api';

interface EndingGroup {
  group_name: string;
  endings: string[];
  frequency: number;
}

interface VocabWord {
  word: string;
  count: number;
}

export function FreestylePage() {
  const [concept, setConcept] = useState<string>('');
  const [prompt, setPrompt] = useState<string>('');
  const [title, setTitle] = useState<string>('');
  const [word, setWord] = useState<string>('');
  const [endingGroups, setEndingGroups] = useState<EndingGroup[]>([]);
  const [selectedEnding, setSelectedEnding] = useState<string | null>(null);

  const [concepts, setConcepts] = useState<string[]>([]);
  const [prompts, setPrompts] = useState<string[]>([]);
  const [titles, setTitles] = useState<string[]>([]);
  const [vocabulary, setVocabulary] = useState<VocabWord[]>([]);

  const [loading, setLoading] = useState(false);
  const [hasData, setHasData] = useState(false);

  // Load initial data
  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [conceptsRes, promptsRes, titlesRes, vocabRes, endingsRes] = await Promise.all([
        api.freestyleConcepts(),
        api.freestylePrompts(),
        api.freestyleTitles(),
        api.freestyleVocabulary(100),
        api.freestyleEndings(),
      ]);

      setConcepts(conceptsRes.concepts);
      setPrompts(promptsRes.prompts);
      setTitles(titlesRes.titles);
      setVocabulary(vocabRes.words);
      setEndingGroups(endingsRes.groups);

      // Check if we have any data
      const dataExists = conceptsRes.concepts.length > 0 ||
                        promptsRes.prompts.length > 0 ||
                        titlesRes.titles.length > 0;
      setHasData(dataExists);

      // Set initial random values
      if (conceptsRes.concepts.length > 0) {
        setConcept(randomItem(conceptsRes.concepts));
      }
      if (promptsRes.prompts.length > 0) {
        setPrompt(randomItem(promptsRes.prompts));
      }
      if (titlesRes.titles.length > 0) {
        setTitle(randomItem(titlesRes.titles));
      }
      if (vocabRes.words.length > 0) {
        setWord(randomItem(vocabRes.words).word);
      }
    } catch (e) {
      console.error('Failed to load freestyle data:', e);
    } finally {
      setLoading(false);
    }
  };

  const randomItem = <T,>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];

  const nextConcept = useCallback(() => {
    if (concepts.length > 0) {
      setConcept(randomItem(concepts));
    }
  }, [concepts]);

  const nextPrompt = useCallback(() => {
    if (prompts.length > 0) {
      setPrompt(randomItem(prompts));
    }
  }, [prompts]);

  const nextTitle = useCallback(() => {
    if (titles.length > 0) {
      setTitle(randomItem(titles));
    }
  }, [titles]);

  const nextWord = useCallback(() => {
    if (vocabulary.length > 0) {
      setWord(randomItem(vocabulary).word);
    }
  }, [vocabulary]);

  const sparkMe = async () => {
    try {
      const result = await api.freestyleSpark();
      // Show the spark result based on type
      switch (result.type) {
        case 'concept':
          setConcept(result.value);
          break;
        case 'prompt':
          setPrompt(result.value);
          break;
        case 'title':
          setTitle(result.value);
          break;
        case 'word':
          setWord(result.value);
          break;
        case 'ending':
          setSelectedEnding(result.value);
          break;
      }
    } catch (e) {
      console.error('Spark failed:', e);
    }
  };

  const selectRandomEnding = () => {
    const allEndings = endingGroups.flatMap(g => g.endings);
    if (allEndings.length > 0) {
      setSelectedEnding(randomItem(allEndings));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-zinc-400">Loading inspiration pool...</div>
      </div>
    );
  }

  if (!hasData) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 p-8 text-center">
        <div className="text-6xl">🎤</div>
        <h2 className="text-2xl font-bold text-white">No inspiration yet!</h2>
        <p className="text-zinc-400 max-w-md">
          Go to the Import page, search for an artist, and scrape some songs to fill your inspiration pool.
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
    <div className="flex flex-col gap-4 p-4 max-w-2xl mx-auto">
      {/* SPARK ME Button */}
      <button
        onClick={sparkMe}
        className="w-full py-8 bg-gradient-to-r from-amber-500 to-orange-500 text-black text-3xl font-bold rounded-xl hover:from-amber-400 hover:to-orange-400 transition-all shadow-lg hover:shadow-xl active:scale-95"
      >
        🎲 SPARK ME
      </button>

      {/* Concept */}
      {concepts.length > 0 && (
        <div className="bg-zinc-800 rounded-lg p-4">
          <div className="flex items-center gap-2 text-zinc-400 text-sm mb-2">
            <span>💡</span>
            <span>CONCEPT</span>
          </div>
          <div className="text-xl text-white font-medium">{concept || '—'}</div>
          <button
            onClick={nextConcept}
            className="mt-2 px-3 py-1 text-sm bg-zinc-700 rounded hover:bg-zinc-600"
          >
            Next
          </button>
        </div>
      )}

      {/* Prompt */}
      {prompts.length > 0 && (
        <div className="bg-zinc-800 rounded-lg p-4">
          <div className="flex items-center gap-2 text-zinc-400 text-sm mb-2">
            <span>❓</span>
            <span>PROMPT</span>
          </div>
          <div className="text-xl text-white font-medium">{prompt || '—'}</div>
          <button
            onClick={nextPrompt}
            className="mt-2 px-3 py-1 text-sm bg-zinc-700 rounded hover:bg-zinc-600"
          >
            Next
          </button>
        </div>
      )}

      {/* Title */}
      {titles.length > 0 && (
        <div className="bg-zinc-800 rounded-lg p-4">
          <div className="flex items-center gap-2 text-zinc-400 text-sm mb-2">
            <span>🎵</span>
            <span>TITLE</span>
          </div>
          <div className="text-xl text-white font-medium">{title || '—'}</div>
          <button
            onClick={nextTitle}
            className="mt-2 px-3 py-1 text-sm bg-zinc-700 rounded hover:bg-zinc-600"
          >
            Next
          </button>
        </div>
      )}

      {/* Rhyme Endings Grid */}
      {endingGroups.length > 0 && (
        <div className="bg-zinc-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2 text-zinc-400 text-sm">
              <span>🔤</span>
              <span>RHYME ENDINGS</span>
            </div>
            <button
              onClick={selectRandomEnding}
              className="px-3 py-1 text-sm bg-zinc-700 rounded hover:bg-zinc-600"
            >
              🔀 Random
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {endingGroups.slice(0, 8).map((group) => (
              group.endings.slice(0, 2).map((ending) => (
                <button
                  key={ending}
                  onClick={() => setSelectedEnding(ending)}
                  className={`px-3 py-2 rounded-lg font-mono text-sm transition-all ${
                    selectedEnding === ending
                      ? 'bg-amber-500 text-black'
                      : 'bg-zinc-700 text-white hover:bg-zinc-600'
                  }`}
                >
                  {ending}
                </button>
              ))
            ))}
          </div>
          {selectedEnding && (
            <div className="mt-3 p-3 bg-zinc-700 rounded">
              <div className="text-amber-400 font-mono text-lg">{selectedEnding}</div>
              <div className="text-zinc-400 text-sm mt-1">
                Find words ending in this pattern!
              </div>
            </div>
          )}
        </div>
      )}

      {/* Word Bomb */}
      {vocabulary.length > 0 && (
        <div className="bg-zinc-800 rounded-lg p-4">
          <div className="flex items-center gap-2 text-zinc-400 text-sm mb-2">
            <span>💣</span>
            <span>WORD BOMB</span>
          </div>
          <div className="text-2xl text-amber-400 font-bold">{word || '—'}</div>
          <button
            onClick={nextWord}
            className="mt-2 px-3 py-1 text-sm bg-zinc-700 rounded hover:bg-zinc-600"
          >
            Next
          </button>
        </div>
      )}

      {/* Stats */}
      <div className="text-center text-zinc-500 text-sm mt-4">
        Pool: {concepts.length} concepts • {prompts.length} prompts • {titles.length} titles • {vocabulary.length} words
      </div>
    </div>
  );
}
