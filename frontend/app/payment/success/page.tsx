import Link from "next/link";

import { verifyMyFatoorahCallback } from "@/lib/api";

interface PageProps {
  searchParams: Promise<{
    paymentId?: string;
    PaymentId?: string;
    invoiceId?: string;
    InvoiceId?: string;
    Id?: string;
  }>;
}

function getStatusUI(paymentStatus: string | undefined) {
  const status = (paymentStatus ?? "").toLowerCase();

  if (status === "paid") {
    return {
      eyebrow: "Payment Confirmed",
      title: "Consultation payment received.",
      toneClass: "text-[#0f6a4b]",
      panelClass: "border-[#bfead9] bg-[#ecfff7]",
      body: "Your booking is confirmed and notifications are being sent to both physicians.",
    };
  }

  if (status === "pending" || status === "initiated") {
    return {
      eyebrow: "Payment Processing",
      title: "We are still verifying your payment.",
      toneClass: "text-[#8b6200]",
      panelClass: "border-[#f2deb2] bg-[#fffaf0]",
      body: "Please refresh this page in a moment. Booking confirmation occurs only after backend verification.",
    };
  }

  return {
    eyebrow: "Payment Status",
    title: "Payment is not confirmed.",
    toneClass: "text-[#8a2d2d]",
    panelClass: "border-[#f0c6c6] bg-[#fff4f4]",
    body: "The payment was cancelled or failed. You can try booking again.",
  };
}

export default async function PaymentSuccessPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const paymentIdentifier =
    params.paymentId ??
    params.PaymentId ??
    params.invoiceId ??
    params.InvoiceId ??
    params.Id ??
    "";

  const verification = paymentIdentifier
    ? await verifyMyFatoorahCallback(paymentIdentifier)
    : {
        success: false,
        errorMessage:
          "Payment identifier is missing from callback URL. Please contact support if payment was already charged.",
      };

  const ui = getStatusUI(verification.data?.payment_status);

  return (
    <div className="container-shell flex flex-1 items-center justify-center py-14 md:py-20">
      <section className="surface-card w-full max-w-2xl p-7 md:p-9">
        <p className={`text-xs font-semibold tracking-[0.16em] uppercase ${ui.toneClass}`}>
          {ui.eyebrow}
        </p>
        <h1 className="title-serif mt-3 text-3xl font-semibold text-[#1b1b1b] md:text-4xl">
          {ui.title}
        </h1>

        <div className={`mt-5 rounded-2xl border p-4 text-sm ${ui.panelClass}`}>
          {verification.success ? (
            <div className="space-y-2 text-[#244255]">
              <p>{ui.body}</p>
              <p>
                Booking reference: <span className="font-semibold">{verification.data?.booking_reference}</span>
              </p>
              <p>
                Payment status: <span className="font-semibold">{verification.data?.payment_status}</span>
              </p>
              <p>
                Booking status: <span className="font-semibold">{verification.data?.booking_status}</span>
              </p>
            </div>
          ) : (
            <p className="text-[#6b2f2f]">{verification.errorMessage}</p>
          )}
        </div>

        <div className="mt-7 flex flex-wrap gap-3">
          <Link
            href="/"
            className="rounded-xl bg-[#00501e] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#006b2b]"
          >
            Back to Home
          </Link>
          <Link
            href="/payment/error"
            className="rounded-xl border border-[#bfcabb] bg-white px-5 py-3 text-sm font-semibold text-[#00501e] transition hover:bg-[#eef4ee]"
          >
            Go to Payment Help
          </Link>
        </div>
      </section>
    </div>
  );
}



