import Link from "next/link";

export default function PaymentErrorPage() {
  return (
    <div className="container-shell flex flex-1 items-center justify-center py-14 md:py-20">
      <section className="surface-card w-full max-w-2xl p-7 md:p-9">
        <p className="text-xs font-semibold tracking-[0.16em] text-[#8a2d2d] uppercase">
          Payment Failed
        </p>
        <h1 className="title-serif mt-3 text-3xl font-semibold text-[#1b1b1b] md:text-4xl">
          We could not complete your payment.
        </h1>
        <div className="mt-5 rounded-2xl border border-[#f0c6c6] bg-[#fff4f4] p-4 text-sm text-[#6b2f2f]">
          Payment may have been cancelled, timed out, or declined by the provider. No booking is considered confirmed until backend verification succeeds.
        </div>

        <div className="mt-7 flex flex-wrap gap-3">
          <Link
            href="/"
            className="rounded-xl bg-[#00501e] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#006b2b]"
          >
            Back to Home
          </Link>
          <Link
            href="/physicians"
            className="rounded-xl border border-[#bfcabb] bg-white px-5 py-3 text-sm font-semibold text-[#00501e] transition hover:bg-[#eef4ee]"
          >
            Browse Physicians
          </Link>
        </div>
      </section>
    </div>
  );
}



