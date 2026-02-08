import { create } from 'zustand';

interface AppState {
  // Loading states
  loading: Record<string, boolean>;
  setLoading: (key: string, val: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
  loading: {},
  setLoading: (key, val) =>
    set((s) => ({ loading: { ...s.loading, [key]: val } })),
}));
