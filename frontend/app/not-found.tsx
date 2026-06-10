import Link from "next/link";

export default function NotFound() {
  return (
    <div className="container-shell flex flex-1 flex-col items-center justify-center py-20 text-center">
      <div className="surface-card max-w-lg p-8">
        <p className="text-xs font-semibold tracking-[0.16em] text-[#3f493e] uppercase">Not Found</p>
        <h1 className="title-serif mt-3 text-3xl font-semibold text-[#1b1b1b]">
          That physician profile is not available.
        </h1>
        <p className="mt-3 text-sm text-[#3f493e]">
          It may have been removed or the link may be incorrect.
        </p>
        <Link
          href="/"
          className="mt-6 inline-flex rounded-xl bg-[#00501e] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#006b2b]"
        >
          Return to landing page
        </Link>
      </div>
    </div>
  );
}



