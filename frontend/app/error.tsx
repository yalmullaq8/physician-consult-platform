"use client";

import Link from "next/link";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="container-shell flex flex-1 items-center justify-center py-20">
      <div className="surface-card w-full max-w-xl p-8 text-center">
        <p className="text-xs font-semibold tracking-[0.16em] text-[#8a2d2d] uppercase">
          Unexpected Error
        </p>
        <h2 className="title-serif mt-3 text-2xl font-semibold text-[#1b1b1b]">
          Something went wrong while loading this page.
        </h2>
        <p className="mt-3 text-sm text-[#3f493e]">
          {error.message || "Please retry. If the issue continues, check backend connectivity."}
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <button
            type="button"
            onClick={reset}
            className="rounded-xl bg-[#00501e] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#006b2b]"
          >
            Retry
          </button>
          <Link
            href="/"
            className="rounded-xl border border-[#bfcabb] bg-white px-5 py-3 text-sm font-semibold text-[#00501e] transition hover:bg-[#eef4ee]"
          >
            Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}



