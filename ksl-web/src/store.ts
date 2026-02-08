import { create } from 'zustand';

type Page = 'freestyle' | 'import' | 'study' | 'songs';

interface AppState {
  // Navigation
  currentPage: Page;
  setPage: (page: Page) => void;

  // Loading states
  loading: Record<string, boolean>;
  setLoading: (key: string, val: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
  currentPage: 'freestyle',
  setPage: (page) => set({ currentPage: page }),

  loading: {},
  setLoading: (key, val) =>
    set((s) => ({ loading: { ...s.loading, [key]: val } })),
}));
