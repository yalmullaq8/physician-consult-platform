"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { createBooking, getPhysicianAvailableSlots } from "@/lib/api";
import { formatPriceNoDecimals } from "@/lib/formatting";
import { AvailableSlot, PhysicianDetail } from "@/types/api";

interface BookingClientProps {
  physician: PhysicianDetail;
}

const WEEKDAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function toLocalDateString(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getTomorrowDateString() {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  return toLocalDateString(date);
}

function getTodayDateString() {
  return toLocalDateString(new Date());
}

function addDaysToDateString(dateValue: string, daysToAdd: number): string {
  const date = new Date(`${dateValue}T00:00:00`);
  date.setDate(date.getDate() + daysToAdd);
  return toLocalDateString(date);
}

function getMonthStartDateString(dateValue: string): string {
  const date = new Date(`${dateValue}T00:00:00`);
  date.setDate(1);
  return toLocalDateString(date);
}

function addMonthsToDateString(monthStartDateValue: string, monthsToAdd: number): string {
  const date = new Date(`${monthStartDateValue}T00:00:00`);
  date.setDate(1);
  date.setMonth(date.getMonth() + monthsToAdd);
  return toLocalDateString(date);
}

function getDaysInMonth(monthStartDateValue: string): number {
  const date = new Date(`${monthStartDateValue}T00:00:00`);
  return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
}

function getWeekdayIndex(monthStartDateValue: string): number {
  const date = new Date(`${monthStartDateValue}T00:00:00`);
  return date.getDay();
}

function formatMonthLabel(monthStartDateValue: string): string {
  const date = new Date(`${monthStartDateValue}T00:00:00`);
  return date.toLocaleDateString([], { month: "long", year: "numeric" });
}

function formatSlotTime(isoDateTime: string): string {
  return new Date(isoDateTime).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatLongDate(dateValue: string): string {
  return new Date(dateValue).toLocaleDateString([], {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function BookingClient({ physician }: BookingClientProps) {
  const [selectedDate, setSelectedDate] = useState(getTomorrowDateString());
  const [visibleMonthStart, setVisibleMonthStart] = useState(
    getMonthStartDateString(getTomorrowDateString()),
  );
  const [slots, setSlots] = useState<AvailableSlot[]>([]);
  const [selectedSlotStart, setSelectedSlotStart] = useState<string>("");
  const [caseSummary, setCaseSummary] = useState("");
  const [requesterName, setRequesterName] = useState("");
  const [requesterSpecialization, setRequesterSpecialization] = useState("");
  const [requesterCountryOfPractice, setRequesterCountryOfPractice] = useState("");
  const [requesterEmail, setRequesterEmail] = useState("");
  const [requesterWhatsappNumber, setRequesterWhatsappNumber] = useState("");
  const [availabilityByDate, setAvailabilityByDate] = useState<Record<string, number>>({});
  const [isLoadingCalendar, setIsLoadingCalendar] = useState(false);
  const [isLoadingSlots, setIsLoadingSlots] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string>("");

  const selectedSlot = useMemo(
    () => slots.find((slot) => slot.start === selectedSlotStart) ?? null,
    [slots, selectedSlotStart],
  );

  const monthDates = useMemo(() => {
    const daysInMonth = getDaysInMonth(visibleMonthStart);
    return Array.from({ length: daysInMonth }, (_, index) =>
      addDaysToDateString(visibleMonthStart, index),
    );
  }, [visibleMonthStart]);

  const calendarCells = useMemo(() => {
    const leadingEmptyCells = getWeekdayIndex(visibleMonthStart);
    const leading = Array.from({ length: leadingEmptyCells }, () => null as string | null);
    const trailingCount = (7 - ((leadingEmptyCells + monthDates.length) % 7)) % 7;
    const trailing = Array.from({ length: trailingCount }, () => null as string | null);
    return [...leading, ...monthDates, ...trailing];
  }, [monthDates, visibleMonthStart]);

  useEffect(() => {
    let isMounted = true;

    async function loadCalendarAvailability() {
      setIsLoadingCalendar(true);

      const responses = await Promise.all(
        monthDates.map((dateValue) => getPhysicianAvailableSlots(physician.slug, dateValue)),
      );

      if (!isMounted) {
        return;
      }

      const nextAvailabilityByDate: Record<string, number> = {};
      monthDates.forEach((dateValue, index) => {
        nextAvailabilityByDate[dateValue] = responses[index]?.slots?.length ?? 0;
      });
      setAvailabilityByDate(nextAvailabilityByDate);
      setIsLoadingCalendar(false);
    }

    loadCalendarAvailability();

    return () => {
      isMounted = false;
    };
  }, [physician.slug, monthDates]);

  useEffect(() => {
    let isMounted = true;

    async function loadSlots() {
      setIsLoadingSlots(true);
      setStatusMessage("");

      const response = await getPhysicianAvailableSlots(physician.slug, selectedDate);
      if (!isMounted) {
        return;
      }

      if (!response) {
        setSlots([]);
        setSelectedSlotStart("");
        setStatusMessage("Unable to load availability right now. Please try again.");
        setIsLoadingSlots(false);
        return;
      }

      const fetchedSlots = response.slots ?? [];
      setSlots(fetchedSlots);
      setSelectedSlotStart((currentValue) =>
        fetchedSlots.some((slot) => slot.start === currentValue) ? currentValue : "",
      );

      setIsLoadingSlots(false);
    }

    loadSlots();

    return () => {
      isMounted = false;
    };
  }, [physician.slug, selectedDate]);

  async function handleConfirmBooking() {
    if (!selectedSlot) {
      setStatusMessage("Please select an available time slot first.");
      return;
    }

    if (!caseSummary.trim()) {
      setStatusMessage("Please provide a brief case summary.");
      return;
    }

    if (!requesterName.trim()) {
      setStatusMessage("Please provide your name.");
      return;
    }

    if (!requesterSpecialization.trim()) {
      setStatusMessage("Please provide your specialization.");
      return;
    }

    if (!requesterCountryOfPractice.trim()) {
      setStatusMessage("Please provide your country of practice.");
      return;
    }

    if (!requesterEmail.trim()) {
      setStatusMessage("Please provide your email.");
      return;
    }

    setIsSubmitting(true);
    setStatusMessage("");

    const result = await createBooking({
      consulting_physician_id: physician.id,
      scheduled_start: selectedSlot.start,
      case_summary: caseSummary.trim(),
      requester_name: requesterName.trim(),
      requester_specialization: requesterSpecialization.trim(),
      requester_country_of_practice: requesterCountryOfPractice.trim(),
      requester_email: requesterEmail.trim().toLowerCase(),
      requester_whatsapp_number: requesterWhatsappNumber.trim(),
    });

    if (!result.success || !result.data?.payment_url) {
      setIsSubmitting(false);
      setStatusMessage(result.errorMessage ?? "Could not create booking.");
      return;
    }

    window.location.href = result.data.payment_url;
  }

  return (
    <div className="container-shell flex flex-1 flex-col gap-6 py-8 md:py-10">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link
          href={`/physicians/${physician.slug}`}
          className="w-fit rounded-full border border-[#bfcabb] bg-white px-4 py-2 text-sm font-semibold text-[#00501e] transition hover:bg-[#eef4ee]"
        >
          Back to profile
        </Link>
        <p className="text-xs font-semibold tracking-[0.16em] text-[#3f493e] uppercase">
          Book Consultation
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
        <section className="surface-card space-y-5 p-5 md:p-7">
          <div className="rounded-2xl border border-[#bfcabb] bg-white p-4">
            <p className="text-xs font-semibold tracking-[0.16em] text-[#3f493e] uppercase">
              Consulting Physician
            </p>
            <h1 className="title-serif mt-2 text-3xl font-semibold text-[#1b1b1b]">
              {physician.full_name}
            </h1>
            <p className="mt-1 text-sm text-[#3f493e]">{physician.professional_title}</p>
            <p className="mt-2 text-sm font-medium text-[#00501e]">
              {physician.specialty.name}
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-[#bfcabb] bg-white p-4">
              <p className="text-xs font-semibold tracking-[0.16em] text-[#3f493e] uppercase">
                Select Date
              </p>
              <div className="mt-3 flex items-center justify-between gap-3">
                <button
                  type="button"
                  onClick={() => setVisibleMonthStart(addMonthsToDateString(visibleMonthStart, -1))}
                  className="rounded-md border border-[#bfcabb] px-2 py-1 text-xs font-semibold text-[#3f493e] transition hover:bg-[#f2f6f2]"
                >
                  Prev
                </button>
                <p className="text-sm font-semibold text-[#1b1b1b]">{formatMonthLabel(visibleMonthStart)}</p>
                <button
                  type="button"
                  onClick={() => setVisibleMonthStart(addMonthsToDateString(visibleMonthStart, 1))}
                  className="rounded-md border border-[#bfcabb] px-2 py-1 text-xs font-semibold text-[#3f493e] transition hover:bg-[#f2f6f2]"
                >
                  Next
                </button>
              </div>
              <div className="mt-3 grid grid-cols-7 gap-1.5">
                {WEEKDAY_LABELS.map((weekdayLabel) => (
                  <div
                    key={weekdayLabel}
                    className="text-center text-[10px] font-semibold tracking-wide text-[#6d776c] uppercase"
                  >
                    {weekdayLabel}
                  </div>
                ))}
                {calendarCells.map((dateValue, index) => {
                  if (!dateValue) {
                    return <div key={`empty-${index}`} className="h-12 rounded-md bg-transparent" />;
                  }

                  const slotCount = availabilityByDate[dateValue] ?? 0;
                  const hasSlots = slotCount > 0;
                  const isSelected = selectedDate === dateValue;
                  const isPastDate = dateValue < getTodayDateString();
                  const isDisabled = isLoadingCalendar || isPastDate || !hasSlots;
                  const dayNumber = dateValue.slice(-2);

                  return (
                    <button
                      key={dateValue}
                      type="button"
                      disabled={isDisabled}
                      onClick={() => setSelectedDate(dateValue)}
                      className={`h-12 rounded-md border text-sm font-semibold transition ${
                        hasSlots && !isPastDate
                          ? "border-[#9cc5a6] bg-[#e6f4ea] text-[#00501e] hover:bg-[#d8ecdf]"
                          : "cursor-not-allowed border-[#d7d7d7] bg-[#efefef] text-[#8f8f8f]"
                      } ${isSelected ? "ring-2 ring-[#00501e]" : ""}`}
                      aria-label={`${dateValue} ${hasSlots ? "available" : "unavailable"}`}
                    >
                      {dayNumber}
                    </button>
                  );
                })}
              </div>
              <div className="mt-3 flex items-center gap-4 text-xs text-[#3f493e]">
                <div className="flex items-center gap-1.5">
                  <span className="inline-block h-3 w-3 rounded-sm bg-[#e6f4ea]" />
                  <span>Has slots</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="inline-block h-3 w-3 rounded-sm bg-[#efefef]" />
                  <span>No slots</span>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-[#bfcabb] bg-white p-4">
              <p className="text-xs font-semibold tracking-[0.16em] text-[#3f493e] uppercase">
                Available Slots
              </p>
              {isLoadingSlots ? (
                <p className="mt-3 text-sm text-[#3f493e]">Loading slots...</p>
              ) : slots.length === 0 ? (
                <p className="mt-3 text-sm text-[#3f493e]">
                  No slots available for this date.
                </p>
              ) : (
                <div className="mt-3 flex flex-wrap gap-2">
                  {slots.map((slot) => {
                    const isSelected = slot.start === selectedSlotStart;
                    return (
                      <button
                        key={slot.start}
                        type="button"
                        onClick={() => setSelectedSlotStart(slot.start)}
                        className={`rounded-lg border px-3 py-2 text-sm font-semibold transition ${
                          isSelected
                            ? "border-[#00501e] bg-[#e6f2e9] text-[#00501e]"
                            : "border-[#bfcabb] bg-white text-[#3f493e] hover:bg-[#f3f3f3]"
                        }`}
                      >
                        {formatSlotTime(slot.start)}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-[#bfcabb] bg-white p-4">
            <label
              htmlFor="case-summary"
              className="text-xs font-semibold tracking-[0.16em] text-[#3f493e] uppercase"
            >
              Case Summary
            </label>
            <textarea
              id="case-summary"
              value={caseSummary}
              onChange={(event) => setCaseSummary(event.target.value)}
              rows={5}
              placeholder="Briefly describe the case and consultation goals."
              className="mt-3 w-full rounded-xl border border-[#bfcabb] bg-[#ffffff] px-3 py-2 text-sm text-[#1b1b1b] outline-none ring-[#00501e] transition focus:ring-2"
            />
          </div>

          <div className="rounded-2xl border border-[#bfcabb] bg-white p-4">
            <p className="text-xs font-semibold tracking-[0.16em] text-[#3f493e] uppercase">
              Requester Details
            </p>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <div>
                <label htmlFor="requester-name" className="text-xs font-semibold text-[#3f493e]">
                  Name
                </label>
                <input
                  id="requester-name"
                  type="text"
                  value={requesterName}
                  onChange={(event) => setRequesterName(event.target.value)}
                  className="mt-1 w-full rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-sm text-[#1b1b1b] outline-none ring-[#00501e] transition focus:ring-2"
                  placeholder="Your full name"
                />
              </div>

              <div>
                <label htmlFor="requester-specialization" className="text-xs font-semibold text-[#3f493e]">
                  Specialization
                </label>
                <input
                  id="requester-specialization"
                  type="text"
                  value={requesterSpecialization}
                  onChange={(event) => setRequesterSpecialization(event.target.value)}
                  className="mt-1 w-full rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-sm text-[#1b1b1b] outline-none ring-[#00501e] transition focus:ring-2"
                  placeholder="e.g. Orthodontics"
                />
              </div>

              <div>
                <label htmlFor="requester-country" className="text-xs font-semibold text-[#3f493e]">
                  Country of Practice
                </label>
                <input
                  id="requester-country"
                  type="text"
                  value={requesterCountryOfPractice}
                  onChange={(event) => setRequesterCountryOfPractice(event.target.value)}
                  className="mt-1 w-full rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-sm text-[#1b1b1b] outline-none ring-[#00501e] transition focus:ring-2"
                  placeholder="e.g. Kuwait"
                />
              </div>

              <div>
                <label htmlFor="requester-email" className="text-xs font-semibold text-[#3f493e]">
                  Email
                </label>
                <input
                  id="requester-email"
                  type="email"
                  value={requesterEmail}
                  onChange={(event) => setRequesterEmail(event.target.value)}
                  className="mt-1 w-full rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-sm text-[#1b1b1b] outline-none ring-[#00501e] transition focus:ring-2"
                  placeholder="you@example.com"
                />
              </div>

              <div className="md:col-span-2">
                <label htmlFor="requester-whatsapp" className="text-xs font-semibold text-[#3f493e]">
                  WhatsApp Number (Optional)
                </label>
                <input
                  id="requester-whatsapp"
                  type="text"
                  value={requesterWhatsappNumber}
                  onChange={(event) => setRequesterWhatsappNumber(event.target.value)}
                  className="mt-1 w-full rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-sm text-[#1b1b1b] outline-none ring-[#00501e] transition focus:ring-2"
                  placeholder="+965 XXXXXXXX"
                />
              </div>
            </div>
          </div>

          {statusMessage ? (
            <p className="rounded-xl border border-[#f0c6c6] bg-[#fff4f4] px-3 py-2 text-sm text-[#8a2d2d]">
              {statusMessage}
            </p>
          ) : null}
        </section>

        <aside className="space-y-4">
          <div className="surface-card p-4 md:p-5">
            <p className="text-xs font-semibold tracking-[0.16em] text-[#3f493e] uppercase">
              Booking Summary
            </p>
            <div className="mt-3 space-y-2 text-sm text-[#3f493e]">
              <p>
                Date: <span className="font-semibold text-[#1b1b1b]">{formatLongDate(selectedDate)}</span>
              </p>
              <p>
                Time: <span className="font-semibold text-[#1b1b1b]">
                  {selectedSlot ? formatSlotTime(selectedSlot.start) : "Select a slot"}
                </span>
              </p>
              <p>
                Fee: <span className="font-semibold text-[#1b1b1b]">
                  {formatPriceNoDecimals(physician.consultation_price)}
                </span>
              </p>
            </div>
            <button
              type="button"
              disabled={isSubmitting}
              onClick={handleConfirmBooking}
              className="mt-4 w-full rounded-xl bg-[#00501e] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#006b2b] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? "Creating booking..." : "Confirm and Pay"}
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}


