import { useStore } from '../store';

const navItems = [
  { id: 'studio' as const, label: 'Studio', icon: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z' },
  { id: 'import' as const, label: 'Import', icon: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12' },
];

export function NavSidebar() {
  const { currentPage, setPage } = useStore();

  return (
    <aside className="w-16 bg-zinc-900 border-r border-zinc-800 flex flex-col items-center py-4 gap-2">
      {navItems.map((item) => (
        <button
          key={item.id}
          onClick={() => setPage(item.id)}
          className={`w-12 h-12 rounded-xl flex flex-col items-center justify-center gap-1 transition-colors ${
            currentPage === item.id
              ? 'bg-amber-500/20 text-amber-400'
              : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800'
          }`}
          title={item.label}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} />
          </svg>
          <span className="text-[10px] font-medium">{item.label}</span>
        </button>
      ))}
    </aside>
  );
}
