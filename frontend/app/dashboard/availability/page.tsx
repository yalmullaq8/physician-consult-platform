"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  createAvailabilityBlock,
  createAvailabilityException,
  deleteAvailabilityBlock,
  deleteAvailabilityException,
  getMyAvailability,
  updateAvailabilityBlock,
  updateAvailabilityException,
} from "@/lib/api";
import { AvailabilityExceptionDraft, WeeklyAvailabilityBlock } from "@/types/api";

const WEEKDAYS = [
  { value: 0, label: "Monday" },
  { value: 1, label: "Tuesday" },
  { value: 2, label: "Wednesday" },
  { value: 3, label: "Thursday" },
  { value: 4, label: "Friday" },
  { value: 5, label: "Saturday" },
  { value: 6, label: "Sunday" },
];

function sortBlocks(blocks: WeeklyAvailabilityBlock[]) {
  return [...blocks].sort(
    (a, b) => a.weekday - b.weekday || a.startTime.localeCompare(b.startTime),
  );
}

export default function AvailabilityPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [statusMessage, setStatusMessage] = useState("");
  const [blocks, setBlocks] = useState<WeeklyAvailabilityBlock[]>([]);
  const [exceptions, setExceptions] = useState<AvailabilityExceptionDraft[]>([]);

  const [weekday, setWeekday] = useState(0);
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("10:00");

  const [exceptionDate, setExceptionDate] = useState("");
  const [exceptionStart, setExceptionStart] = useState("09:00");
  const [exceptionEnd, setExceptionEnd] = useState("10:00");
  const [exceptionType, setExceptionType] = useState<"unavailable" | "extra_available">("unavailable");
  const [exceptionReason, setExceptionReason] = useState("");

  const [editingBlockId, setEditingBlockId] = useState<string | null>(null);
  const [editBlockWeekday, setEditBlockWeekday] = useState(0);
  const [editBlockStartTime, setEditBlockStartTime] = useState("09:00");
  const [editBlockEndTime, setEditBlockEndTime] = useState("10:00");

  const [editingExceptionId, setEditingExceptionId] = useState<string | null>(null);
  const [editExceptionDate, setEditExceptionDate] = useState("");
  const [editExceptionStartTime, setEditExceptionStartTime] = useState("09:00");
  const [editExceptionEndTime, setEditExceptionEndTime] = useState("10:00");
  const [editExceptionType, setEditExceptionType] = useState<"unavailable" | "extra_available">("unavailable");
  const [editExceptionReason, setEditExceptionReason] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadAvailability() {
      setIsLoading(true);
      const response = await getMyAvailability();
      if (!mounted) {
        return;
      }

      if (!response.success) {
        setStatusMessage(response.errorMessage ?? "Could not load availability.");
        setIsLoading(false);
        return;
      }

      setBlocks(
        sortBlocks(
          response.data.blocks.map((block) => ({
            id: String(block.id),
            weekday: block.weekday,
            startTime: block.start_time.slice(0, 5),
            endTime: block.end_time.slice(0, 5),
          })),
        ),
      );
      setExceptions(
        response.data.exceptions.map((item) => ({
          id: String(item.id),
          date: item.date,
          startTime: item.start_time.slice(0, 5),
          endTime: item.end_time.slice(0, 5),
          exceptionType: item.exception_type,
          reason: item.reason,
        })),
      );
      setIsLoading(false);
    }

    loadAvailability();
    return () => {
      mounted = false;
    };
  }, []);

  async function addWeeklyBlock() {
    if (startTime >= endTime) {
      setStatusMessage("Start time must be before end time.");
      return;
    }

    const overlapExists = blocks.some(
      (block) =>
        block.weekday === weekday &&
        block.startTime < endTime &&
        block.endTime > startTime,
    );

    if (overlapExists) {
      setStatusMessage("This time range overlaps another block on the same day.");
      return;
    }

    const result = await createAvailabilityBlock({
      weekday,
      start_time: startTime,
      end_time: endTime,
      is_active: true,
    });
    if (!result.success || !result.data) {
      setStatusMessage(result.errorMessage ?? "Could not create block.");
      return;
    }

    const next = sortBlocks([...blocks, {
      id: String(result.data.id),
      weekday: result.data.weekday,
      startTime: result.data.start_time.slice(0, 5),
      endTime: result.data.end_time.slice(0, 5),
    }]);

    setBlocks(next);
    setStatusMessage("Weekly block saved.");
  }

  async function removeBlock(id: string) {
    const result = await deleteAvailabilityBlock(Number(id));
    if (!result.success) {
      setStatusMessage(result.errorMessage ?? "Could not remove block.");
      return;
    }

    const next = blocks.filter((block) => block.id !== id);
    setBlocks(next);
    setStatusMessage("Weekly block removed.");
  }

  function startEditBlock(id: string) {
    const block = blocks.find((item) => item.id === id);
    if (!block) {
      return;
    }
    setEditingBlockId(id);
    setEditBlockWeekday(block.weekday);
    setEditBlockStartTime(block.startTime);
    setEditBlockEndTime(block.endTime);
  }

  function cancelEditBlock() {
    setEditingBlockId(null);
  }

  async function saveEditBlock() {
    if (!editingBlockId) {
      return;
    }
    if (editBlockStartTime >= editBlockEndTime) {
      setStatusMessage("Start time must be before end time.");
      return;
    }

    const result = await updateAvailabilityBlock(Number(editingBlockId), {
      weekday: editBlockWeekday,
      start_time: editBlockStartTime,
      end_time: editBlockEndTime,
    });
    if (!result.success || !result.data) {
      setStatusMessage(result.errorMessage ?? "Could not update block.");
      return;
    }
    const updatedBlock = result.data;

    setBlocks(
      sortBlocks(
        blocks.map((item) =>
          item.id === editingBlockId
            ? {
                id: String(updatedBlock.id),
                weekday: updatedBlock.weekday,
                startTime: updatedBlock.start_time.slice(0, 5),
                endTime: updatedBlock.end_time.slice(0, 5),
              }
            : item,
        ),
      ),
    );
    setEditingBlockId(null);
    setStatusMessage("Weekly block updated.");
  }

  async function addException() {
    if (!exceptionDate) {
      setStatusMessage("Please select an exception date.");
      return;
    }
    if (exceptionStart >= exceptionEnd) {
      setStatusMessage("Exception start time must be before end time.");
      return;
    }

    const result = await createAvailabilityException({
      date: exceptionDate,
      start_time: exceptionStart,
      end_time: exceptionEnd,
      exception_type: exceptionType,
      reason: exceptionReason.trim(),
    });
    if (!result.success || !result.data) {
      setStatusMessage(result.errorMessage ?? "Could not create exception.");
      return;
    }

    const next = [...exceptions, {
      id: String(result.data.id),
      date: result.data.date,
      startTime: result.data.start_time.slice(0, 5),
      endTime: result.data.end_time.slice(0, 5),
      exceptionType: result.data.exception_type,
      reason: result.data.reason,
    }].sort((a, b) => a.date.localeCompare(b.date) || a.startTime.localeCompare(b.startTime));

    setExceptions(next);
    setStatusMessage("Availability exception saved.");
  }

  async function removeException(id: string) {
    const result = await deleteAvailabilityException(Number(id));
    if (!result.success) {
      setStatusMessage(result.errorMessage ?? "Could not remove exception.");
      return;
    }

    const next = exceptions.filter((item) => item.id !== id);
    setExceptions(next);
    setStatusMessage("Availability exception removed.");
  }

  function startEditException(id: string) {
    const item = exceptions.find((entry) => entry.id === id);
    if (!item) {
      return;
    }

    setEditingExceptionId(id);
    setEditExceptionDate(item.date);
    setEditExceptionStartTime(item.startTime);
    setEditExceptionEndTime(item.endTime);
    setEditExceptionType(item.exceptionType);
    setEditExceptionReason(item.reason);
  }

  function cancelEditException() {
    setEditingExceptionId(null);
  }

  async function saveEditException() {
    if (!editingExceptionId) {
      return;
    }
    if (!editExceptionDate) {
      setStatusMessage("Please select an exception date.");
      return;
    }
    if (editExceptionStartTime >= editExceptionEndTime) {
      setStatusMessage("Exception start time must be before end time.");
      return;
    }

    const result = await updateAvailabilityException(Number(editingExceptionId), {
      date: editExceptionDate,
      start_time: editExceptionStartTime,
      end_time: editExceptionEndTime,
      exception_type: editExceptionType,
      reason: editExceptionReason.trim(),
    });
    if (!result.success || !result.data) {
      setStatusMessage(result.errorMessage ?? "Could not update exception.");
      return;
    }
    const updatedException = result.data;

    setExceptions(
      exceptions
        .map((item) =>
          item.id === editingExceptionId
            ? {
                id: String(updatedException.id),
                date: updatedException.date,
                startTime: updatedException.start_time.slice(0, 5),
                endTime: updatedException.end_time.slice(0, 5),
                exceptionType: updatedException.exception_type,
                reason: updatedException.reason,
              }
            : item,
        )
        .sort((a, b) => a.date.localeCompare(b.date) || a.startTime.localeCompare(b.startTime)),
    );
    setEditingExceptionId(null);
    setStatusMessage("Availability exception updated.");
  }

  function clearDraft() {
    setBlocks([]);
    setExceptions([]);
    setStatusMessage(
      "Local page state cleared. Existing records remain on the server; remove each item to delete permanently.",
    );
  }

  return (
    <div className="container-shell flex flex-1 flex-col gap-6 py-8 md:py-10">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold tracking-[0.16em] text-[#3f493e] uppercase">Dashboard</p>
          <h1 className="title-serif mt-2 text-4xl font-semibold text-[#1b1b1b] md:text-5xl">
            Availability Management
          </h1>
          <p className="mt-3 text-sm text-[#3f493e] md:text-base">
            Build your weekly availability schedule and date-specific exceptions.
          </p>
        </div>

        <Link
          href="/dashboard"
          className="rounded-full border border-[#bfcabb] bg-white px-4 py-2 text-sm font-semibold text-[#00501e] transition hover:bg-[#eef4ee]"
        >
          Back to Dashboard
        </Link>
      </header>

      <section className="surface-card border border-[#bfcabb] bg-[#f3f3f3] p-4 text-sm text-[#3f493e]">
        Changes on this page are saved directly to your physician availability records via authenticated API calls.
      </section>

      {isLoading ? (
        <section className="surface-card p-5 text-sm text-[#3f493e]">Loading availability...</section>
      ) : null}

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="surface-card p-5">
          <h2 className="text-lg font-semibold text-[#1b1b1b]">Weekly Availability</h2>

          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <select
              value={weekday}
              onChange={(event) => setWeekday(Number(event.target.value))}
              className="rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-sm"
            >
              {WEEKDAYS.map((day) => (
                <option key={day.value} value={day.value}>
                  {day.label}
                </option>
              ))}
            </select>

            <input
              type="time"
              value={startTime}
              onChange={(event) => setStartTime(event.target.value)}
              className="rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-sm"
            />

            <input
              type="time"
              value={endTime}
              onChange={(event) => setEndTime(event.target.value)}
              className="rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-sm"
            />
          </div>

          <button
            type="button"
            onClick={addWeeklyBlock}
            className="mt-3 rounded-xl bg-[#00501e] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#006b2b]"
          >
            Add Weekly Block
          </button>

          <div className="mt-4 space-y-2">
            {blocks.length === 0 ? (
              <p className="text-sm text-[#3f493e]">No weekly blocks yet.</p>
            ) : (
              blocks.map((block) => (
                <div key={block.id} className="flex items-center justify-between rounded-xl border border-[#bfcabb] bg-white px-3 py-2">
                  {editingBlockId === block.id ? (
                    <div className="w-full space-y-2">
                      <div className="grid gap-2 sm:grid-cols-3">
                        <select
                          value={editBlockWeekday}
                          onChange={(event) => setEditBlockWeekday(Number(event.target.value))}
                          className="rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-xs"
                        >
                          {WEEKDAYS.map((day) => (
                            <option key={day.value} value={day.value}>
                              {day.label}
                            </option>
                          ))}
                        </select>
                        <input
                          type="time"
                          value={editBlockStartTime}
                          onChange={(event) => setEditBlockStartTime(event.target.value)}
                          className="rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-xs"
                        />
                        <input
                          type="time"
                          value={editBlockEndTime}
                          onChange={(event) => setEditBlockEndTime(event.target.value)}
                          className="rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-xs"
                        />
                      </div>
                      <div className="flex items-center gap-2">
                        <button type="button" onClick={saveEditBlock} className="text-xs font-semibold text-[#00501e]">
                          Save
                        </button>
                        <button type="button" onClick={cancelEditBlock} className="text-xs font-semibold text-[#3f493e]">
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <p className="text-sm text-[#1b1b1b]">
                        {WEEKDAYS.find((day) => day.value === block.weekday)?.label}: {block.startTime} - {block.endTime}
                      </p>
                      <div className="flex items-center gap-3">
                        <button type="button" onClick={() => startEditBlock(block.id)} className="text-xs font-semibold text-[#00501e]">
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => removeBlock(block.id)}
                          className="text-xs font-semibold text-[#9b3d3d]"
                        >
                          Remove
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        <div className="surface-card p-5">
          <h2 className="text-lg font-semibold text-[#1b1b1b]">Date Exceptions</h2>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <input
              type="date"
              value={exceptionDate}
              onChange={(event) => setExceptionDate(event.target.value)}
              className="rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-sm"
            />
            <select
              value={exceptionType}
              onChange={(event) => setExceptionType(event.target.value as "unavailable" | "extra_available")}
              className="rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-sm"
            >
              <option value="unavailable">Unavailable</option>
              <option value="extra_available">Extra Available</option>
            </select>
            <input
              type="time"
              value={exceptionStart}
              onChange={(event) => setExceptionStart(event.target.value)}
              className="rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-sm"
            />
            <input
              type="time"
              value={exceptionEnd}
              onChange={(event) => setExceptionEnd(event.target.value)}
              className="rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-sm"
            />
          </div>

          <textarea
            value={exceptionReason}
            onChange={(event) => setExceptionReason(event.target.value)}
            rows={3}
            placeholder="Optional reason"
            className="mt-3 w-full rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-sm"
          />

          <button
            type="button"
            onClick={addException}
            className="mt-3 rounded-xl bg-[#00501e] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#006b2b]"
          >
            Add Exception
          </button>

          <div className="mt-4 space-y-2">
            {exceptions.length === 0 ? (
              <p className="text-sm text-[#3f493e]">No exceptions yet.</p>
            ) : (
              exceptions.map((item) => (
                <div key={item.id} className="rounded-xl border border-[#bfcabb] bg-white px-3 py-2">
                  {editingExceptionId === item.id ? (
                    <div className="space-y-2">
                      <div className="grid gap-2 sm:grid-cols-2">
                        <input
                          type="date"
                          value={editExceptionDate}
                          onChange={(event) => setEditExceptionDate(event.target.value)}
                          className="rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-xs"
                        />
                        <select
                          value={editExceptionType}
                          onChange={(event) => setEditExceptionType(event.target.value as "unavailable" | "extra_available")}
                          className="rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-xs"
                        >
                          <option value="unavailable">Unavailable</option>
                          <option value="extra_available">Extra Available</option>
                        </select>
                        <input
                          type="time"
                          value={editExceptionStartTime}
                          onChange={(event) => setEditExceptionStartTime(event.target.value)}
                          className="rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-xs"
                        />
                        <input
                          type="time"
                          value={editExceptionEndTime}
                          onChange={(event) => setEditExceptionEndTime(event.target.value)}
                          className="rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-xs"
                        />
                      </div>
                      <input
                        type="text"
                        value={editExceptionReason}
                        onChange={(event) => setEditExceptionReason(event.target.value)}
                        placeholder="Reason"
                        className="w-full rounded-xl border border-[#bfcabb] bg-white px-3 py-2 text-xs"
                      />
                      <div className="flex items-center gap-2">
                        <button type="button" onClick={saveEditException} className="text-xs font-semibold text-[#00501e]">
                          Save
                        </button>
                        <button type="button" onClick={cancelEditException} className="text-xs font-semibold text-[#3f493e]">
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-semibold text-[#1b1b1b]">
                          {item.date} - {item.startTime} to {item.endTime}
                        </p>
                        <div className="flex items-center gap-3">
                          <button type="button" onClick={() => startEditException(item.id)} className="text-xs font-semibold text-[#00501e]">
                            Edit
                          </button>
                          <button
                            type="button"
                            onClick={() => removeException(item.id)}
                            className="text-xs font-semibold text-[#9b3d3d]"
                          >
                            Remove
                          </button>
                        </div>
                      </div>
                      <p className="mt-1 text-xs text-[#3f493e]">
                        {item.exceptionType === "unavailable" ? "Unavailable" : "Extra Available"}
                        {item.reason ? ` - ${item.reason}` : ""}
                      </p>
                    </>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </section>

      <section className="surface-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-[#3f493e]">
            Current records: {blocks.length} weekly blocks, {exceptions.length} exceptions.
          </p>
          <button
            type="button"
            onClick={clearDraft}
            className="rounded-lg border border-[#efc4c4] bg-[#fff4f4] px-3 py-2 text-sm font-semibold text-[#8a2d2d] transition hover:bg-[#ffeaea]"
          >
            Clear Draft
          </button>
        </div>
      </section>

      {statusMessage ? (
        <p className="rounded-xl border border-[#bfcabb] bg-white px-4 py-2 text-sm text-[#3f493e]">
          {statusMessage}
        </p>
      ) : null}
    </div>
  );
}



