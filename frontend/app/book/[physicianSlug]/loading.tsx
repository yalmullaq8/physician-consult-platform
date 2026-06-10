export default function BookingLoading() {
  return (
    <div className="container-shell flex flex-1 flex-col gap-6 py-8 md:py-10">
      <div className="surface-card h-16 animate-pulse" />
      <div className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
        <div className="surface-card h-[420px] animate-pulse" />
        <div className="surface-card h-[420px] animate-pulse" />
      </div>
    </div>
  );
}


