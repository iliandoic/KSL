const BASE = '/api';

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API error ${res.status}: ${err}`);
  }
  return res.json();
}

export const api = {
  syllables: (line: string) =>
    post<{ count: number; words: { word: string; syllables: number }[] }>('/syllables', { line }),

  rhymes: (word: string) =>
    post<{ word: string; perfect: string[]; near: string[]; slant: string[] }>('/rhymes', { word }),

  complete: (lines: string[], theme?: string, count = 3) =>
    post<{ suggestions: string[] }>('/complete', { lines, theme, count }),

  corpusIngest: (text: string, source?: string) =>
    post<{ lines_added: number; themes_detected: Record<string, number>; words_added: number }>('/corpus/ingest', { text, source }),

  corpusIngestUrl: (url: string) =>
    post<{ title: string; artist: string; lines_added: number; words_added: number; themes_detected: Record<string, number> }>('/corpus/ingest-url', { url }),

  corpusSearch: (params: { theme?: string; syllables?: number; query?: string }) =>
    post<{ lines: { line: string; source: string; theme: string; syllables: number }[] }>('/corpus/search', params),

  sparkTitles: (theme?: string) =>
    post<{ titles: string[] }>('/spark/titles', { theme }),

  sparkFromTitle: (title: string) =>
    post<{ opening_lines: string[] }>('/spark/from-title', { title }),

  sparkRandom: () =>
    post<{ spark: string; type: string }>('/spark/random', {}),

  sparkExplode: (word: string) =>
    post<{
      starts_with: string[];
      ends_with: string[];
      rhymes: string[];
      combos: string[];
    }>('/spark/explode', { word }),

  styleImport: (text: string, mode: string, source?: string) =>
    post<{ status: string; details: Record<string, unknown> }>('/style/import', { text, mode, source }),
};
