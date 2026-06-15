export default function PhysiciansLoading() {
  return (
    <div className="container-shell flex flex-1 flex-col gap-5 py-8 md:py-10">
      <div className="surface-card h-24 animate-pulse" />
      <div className="surface-card h-24 animate-pulse" />
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div className="surface-card h-56 animate-pulse" />
        <div className="surface-card h-56 animate-pulse" />
        <div className="surface-card h-56 animate-pulse" />
      </div>
    </div>
  );
}



