"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { getCurrentUser, getMyBookings } from "@/lib/api";
import { BookingRecord } from "@/types/api";

type BookingBucket = "upcoming" | "past";

function splitBookings(bookings: BookingRecord[]) {
  const now = new Date();
  const upcoming: BookingRecord[] = [];
  const past: BookingRecord[] = [];

  for (const booking of bookings) {
    if (new Date(booking.scheduled_start) >= now) {
      upcoming.push(booking);
    } else {
      past.push(booking);
    }
  }

  return { upcoming, past };
}

function formatDateTime(dateValue: string) {
  return new Date(dateValue).toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function prettyStatus(status: string) {
  return status.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function statusClass(status: string) {
  const normalized = status.toLowerCase();
  if (["confirmed", "completed", "paid"].includes(normalized)) {
    return "bg-[#e7fff7] text-[#0f5f45] border-[#bde9d7]";
  }
  if (["pending_payment", "draft"].includes(normalized)) {
    return "bg-[#fff7e8] text-[#805700] border-[#f3dfb6]";
  }
  return "bg-[#fff1f1] text-[#8a2d2d] border-[#efc4c4]";
}

function BookingCard({ booking }: { booking: BookingRecord }) {
  return (
    <article className="surface-card rounded-2xl p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold tracking-[0.16em] text-[#3f493e] uppercase">
            {booking.booking_reference}
          </p>
          <h3 className="mt-2 text-lg font-semibold text-[#1b1b1b]">
            {booking.consulting_physician_name}
          </h3>
          <p className="mt-1 text-sm text-[#3f493e]">{formatDateTime(booking.scheduled_start)}</p>
        </div>

        <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${statusClass(booking.status)}`}>
          {prettyStatus(booking.status)}
        </span>
      </div>

      <p className="mt-3 line-clamp-2 text-sm text-[#3f493e]">{booking.case_summary}</p>

      {booking.meeting_url ? (
        <a
          href={booking.meeting_url}
          target="_blank"
          rel="noreferrer"
          className="mt-4 inline-flex rounded-lg border border-[#bfcabb] px-3 py-2 text-sm font-semibold text-[#00501e] transition hover:bg-[#eef4ee]"
        >
          Open Meeting Link
        </a>
      ) : null}
    </article>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [activeBucket, setActiveBucket] = useState<BookingBucket>("upcoming");
  const [bookings, setBookings] = useState<BookingRecord[]>([]);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadDashboard() {
      const auth = await getCurrentUser();
      if (!mounted) {
        return;
      }

      if (!auth.success) {
        router.replace("/login?next=/dashboard");
        return;
      }

      setIsLoading(true);
      const response = await getMyBookings();
      if (!mounted) {
        return;
      }

      setBookings(response.data);
      setErrorMessage(response.success ? "" : response.errorMessage ?? "Unable to load bookings.");
      setIsLoading(false);
    }

    loadDashboard();
    return () => {
      mounted = false;
    };
  }, [router]);

  const { upcoming, past } = useMemo(() => splitBookings(bookings), [bookings]);
  const activeList = activeBucket === "upcoming" ? upcoming : past;

  return (
    <div className="container-shell flex flex-1 flex-col gap-6 py-8 md:py-10">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold tracking-[0.16em] text-[#3f493e] uppercase">Dashboard</p>
          <h1 className="title-serif mt-2 text-4xl font-semibold text-[#1b1b1b] md:text-5xl">
            Consultation Timeline
          </h1>
          <p className="mt-3 text-sm text-[#3f493e] md:text-base">
            Review upcoming and completed consults, payment progress, and meeting links.
          </p>
        </div>

        <Link
          href="/dashboard/availability"
          className="rounded-xl bg-[#00501e] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#006b2b]"
        >
          Manage Availability
        </Link>
      </header>

      <section className="surface-card p-5 md:p-6">
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => setActiveBucket("upcoming")}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
              activeBucket === "upcoming"
                ? "bg-[#00501e] text-white"
                : "border border-[#bfcabb] bg-white text-[#00501e] hover:bg-[#eef4ee]"
            }`}
          >
            Upcoming ({upcoming.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveBucket("past")}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
              activeBucket === "past"
                ? "bg-[#00501e] text-white"
                : "border border-[#bfcabb] bg-white text-[#00501e] hover:bg-[#eef4ee]"
            }`}
          >
            Past ({past.length})
          </button>
        </div>
      </section>

      {isLoading ? (
        <section className="surface-card p-6">
          <p className="text-sm text-[#3f493e]">Loading your bookings...</p>
        </section>
      ) : errorMessage ? (
        <section className="surface-card border border-[#efc4c4] bg-[#fff4f4] p-6">
          <p className="text-sm text-[#8a2d2d]">{errorMessage}</p>
          <p className="mt-2 text-xs text-[#7b4444]">
            Make sure you are authenticated in the backend session before opening this page.
          </p>
        </section>
      ) : activeList.length === 0 ? (
        <section className="surface-card p-6">
          <p className="text-sm text-[#3f493e]">
            {activeBucket === "upcoming"
              ? "No upcoming consultations found."
              : "No past consultations found yet."}
          </p>
          <Link
            href="/physicians"
            className="mt-4 inline-flex rounded-xl bg-[#00501e] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#006b2b]"
          >
            Browse Consultants
          </Link>
        </section>
      ) : (
        <section className="grid gap-4 md:grid-cols-2">
          {activeList.map((booking) => (
            <BookingCard key={booking.booking_reference} booking={booking} />
          ))}
        </section>
      )}
    </div>
  );
}



