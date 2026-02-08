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

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
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

  corpusIngest: (text: string, source?: string, sections?: { section: string; lines: string[] }[], title?: string, url?: string) =>
    post<{ lines_added: number; themes_detected: Record<string, number>; words_added: number; sections_found: Record<string, number>; song_id: number | null }>('/corpus/ingest', { text, source, sections, title, url }),

  corpusIngestUrl: (url: string) =>
    post<{ title: string; artist: string; lines_added: number; words_added: number; themes_detected: Record<string, number> }>('/corpus/ingest-url', { url }),

  corpusScrapeUrl: (url: string) =>
    post<{ title: string; artist: string; lyrics: string; sections: { section: string; lines: string[] }[]; url: string }>('/corpus/scrape-url', { url }),

  corpusSearch: (params: { theme?: string; syllables?: number; query?: string; section?: string }) =>
    post<{ lines: { line: string; source: string; theme: string; section: string; syllables: number }[] }>('/corpus/search', params),

  corpusStats: () =>
    get<{
      total_lines: number;
      total_songs: number;
      sections: Record<string, number>;
      songs_with_hooks: number;
      songs_with_intro: number;
      songs_with_outro: number;
      songs_with_bridge: number;
    }>('/corpus/stats'),

  corpusSongs: (limit = 50) =>
    get<{
      songs: {
        id: number;
        title: string;
        artist: string;
        url: string;
        hook_count: number;
        verse_count: number;
        has_intro: boolean;
        has_outro: boolean;
        has_bridge: boolean;
        total_lines: number;
      }[];
    }>(`/corpus/songs?limit=${limit}`),

  translate: (lines: string[], targetLang: string = 'en', model: 'sonnet' | 'opus' = 'sonnet') =>
    post<{ translations: string[] }>('/corpus/translate', { lines, target_lang: targetLang, model }),

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

  // Scraped songs
  scrapedSave: (data: {
    title: string;
    artist: string;
    url: string;
    original_text: string;
    sections: { section: string; lines: string[] }[];
    sonnet_translations: Record<string, string>;
    opus_translations: Record<string, string>;
  }) => post<{ id: number; status: string }>('/scraped/save', data),

  scrapedList: () =>
    get<{
      songs: {
        id: number;
        title: string;
        artist: string;
        url: string;
        has_sonnet: boolean;
        has_opus: boolean;
        created_at: string;
        updated_at: string;
      }[];
    }>('/scraped/list'),

  scrapedGet: (id: number) =>
    get<{
      id: number;
      title: string;
      artist: string;
      url: string;
      original_text: string;
      sections: { section: string; lines: string[] }[];
      sonnet_translations: Record<string, string>;
      opus_translations: Record<string, string>;
      created_at: string;
      updated_at: string;
    }>(`/scraped/${id}`),

  scrapedDelete: (id: number) =>
    fetch(`${BASE}/scraped/${id}`, { method: 'DELETE' }).then(r => r.json()),

  // Genius API
  geniusSearchArtists: (q: string) =>
    get<{ artists: { id: number; name: string; image_url: string }[] }>(`/genius/search/artists?q=${encodeURIComponent(q)}`),

  geniusArtistSongs: (artistId: number, limit = 50) =>
    get<{
      songs: {
        id: number;
        title: string;
        url: string;
        primary_artist: string;
        release_date: string;
      }[];
    }>(`/genius/artists/${artistId}/songs?limit=${limit}`),

  // Atomic scrape + translate + save + study
  scrapeAndStudy: (url: string, model: 'sonnet' | 'opus' = 'sonnet') =>
    post<{
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
    }>('/corpus/scrape-and-study', { url, model }),

  // Study API
  studyArtists: () =>
    get<{ artists: { artist: string; songs_studied: number }[] }>('/study/artists'),

  studyArtist: (artist: string) =>
    get<{
      artist: string;
      songs_studied: number;
      vocabulary: Record<string, number>;
      concepts: string[];
      prompts: string[];
      titles: string[];
      rhyme_groups: {
        group_name: string;
        endings: string[];
        example_words: Record<string, string[]>;
        frequency: number;
      }[];
    }>(`/study/${encodeURIComponent(artist)}`),

  studyLearn: (scrapedSongId: number) =>
    post<{
      artist: string;
      title: string;
      endings_added: number;
      vocabulary_added: number;
      concepts_added: number;
      prompts_added: number;
    }>('/study/learn', { scraped_song_id: scrapedSongId }),

  // Freestyle API
  freestyleSpark: () =>
    get<{ type: string; value: string; group?: string }>('/freestyle/spark'),

  freestyleConcepts: () =>
    get<{ concepts: string[] }>('/freestyle/concepts'),

  freestylePrompts: () =>
    get<{ prompts: string[] }>('/freestyle/prompts'),

  freestyleTitles: () =>
    get<{ titles: string[] }>('/freestyle/titles'),

  freestyleVocabulary: (limit = 50) =>
    get<{ words: { word: string; count: number }[] }>(`/freestyle/vocabulary?limit=${limit}`),

  freestyleEndings: () =>
    get<{ groups: { group_name: string; endings: string[]; frequency: number }[] }>('/freestyle/endings'),
};
