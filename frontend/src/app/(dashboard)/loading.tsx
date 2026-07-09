export default function DashboardLoading() {
  return (
    <div className="flex-1 flex items-center justify-center px-4 py-12">
      <div className="flex flex-col items-center gap-3">
        <div className="w-8 h-8 rounded-full border-2 border-slate-700 border-t-sky-400 animate-spin" />
        <p className="text-xs text-muted-foreground animate-pulse">Loading…</p>
      </div>
    </div>
  );
}
