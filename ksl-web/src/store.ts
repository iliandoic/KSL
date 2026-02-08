import { create } from 'zustand';

interface EditorLine {
  text: string;
  syllables: number | null;
}

type Page = 'studio' | 'import';

interface AppState {
  // Navigation
  currentPage: Page;
  setPage: (page: Page) => void;

  // Editor
  lines: EditorLine[];
  theme: string;
  suggestions: string[];
  setLine: (index: number, text: string) => void;
  setSyllables: (index: number, count: number) => void;
  addLine: () => void;
  removeLine: (index: number) => void;
  setTheme: (theme: string) => void;
  setSuggestions: (suggestions: string[]) => void;
  insertSuggestion: (text: string) => void;

  // Spark
  sparkTab: 'titles' | 'random' | 'explode';
  setSparkTab: (tab: 'titles' | 'random' | 'explode') => void;

  // Loading states
  loading: Record<string, boolean>;
  setLoading: (key: string, val: boolean) => void;
}

export const useStore = create<AppState>((set, get) => ({
  currentPage: 'studio',
  setPage: (page) => set({ currentPage: page }),

  lines: [{ text: '', syllables: null }],
  theme: '',
  suggestions: [],
  sparkTab: 'titles',
  loading: {},

  setLine: (index, text) =>
    set((s) => {
      const lines = [...s.lines];
      lines[index] = { ...lines[index], text };
      return { lines };
    }),

  setSyllables: (index, count) =>
    set((s) => {
      const lines = [...s.lines];
      lines[index] = { ...lines[index], syllables: count };
      return { lines };
    }),

  addLine: () =>
    set((s) => ({ lines: [...s.lines, { text: '', syllables: null }] })),

  removeLine: (index) =>
    set((s) => {
      if (s.lines.length <= 1) return s;
      return { lines: s.lines.filter((_, i) => i !== index) };
    }),

  setTheme: (theme) => set({ theme }),
  setSuggestions: (suggestions) => set({ suggestions }),

  insertSuggestion: (text) =>
    set((s) => {
      // Find first empty line or add new one
      const emptyIdx = s.lines.findIndex((l) => !l.text.trim());
      if (emptyIdx >= 0) {
        const lines = [...s.lines];
        lines[emptyIdx] = { text, syllables: null };
        return { lines, suggestions: [] };
      }
      return { lines: [...s.lines, { text, syllables: null }], suggestions: [] };
    }),

  setSparkTab: (tab) => set({ sparkTab: tab }),

  setLoading: (key, val) =>
    set((s) => ({ loading: { ...s.loading, [key]: val } })),
}));
