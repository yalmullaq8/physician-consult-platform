export default function GlobalLoading() {
  return (
    <div className="container-shell flex flex-1 items-center justify-center py-20">
      <div className="surface-card w-full max-w-xl p-8 text-center">
        <p className="text-xs font-semibold tracking-[0.16em] text-[#3f493e] uppercase">
          Loading
        </p>
        <h2 className="title-serif mt-3 text-2xl font-semibold text-[#1b1b1b]">
          Preparing your consultation experience...
        </h2>
        <div className="mt-6 h-2 overflow-hidden rounded-full bg-[#d8e3d9]">
          <div className="h-full w-1/2 animate-pulse rounded-full bg-[#00501e]" />
        </div>
      </div>
    </div>
  );
}



