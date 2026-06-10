from datetime import date, datetime, timedelta

from django.utils import timezone

from bookings.models import Booking

from .models import AvailabilityException, PhysicianAvailability, PhysicianProfile


BLOCKING_BOOKING_STATUSES = {"pending_payment", "confirmed", "completed", "no_show"}


def _subtract_intervals(base_intervals, removal_intervals):
    result = base_intervals[:]

    for removal_start, removal_end in removal_intervals:
        next_result = []
        for interval_start, interval_end in result:
            if removal_end <= interval_start or removal_start >= interval_end:
                next_result.append((interval_start, interval_end))
                continue

            if removal_start > interval_start:
                next_result.append((interval_start, removal_start))
            if removal_end < interval_end:
                next_result.append((removal_end, interval_end))

        result = next_result

    return sorted(result, key=lambda x: x[0])


def _has_overlap(start_a, end_a, start_b, end_b):
    return start_a < end_b and start_b < end_a


def generate_available_slots(physician: PhysicianProfile, target_date: date):
    tz = timezone.get_current_timezone()
    now = timezone.localtime()

    if not physician.consultation_duration_minutes:
        return []

    weekday = target_date.weekday()

    intervals = []
    availabilities = PhysicianAvailability.objects.filter(
        physician=physician,
        weekday=weekday,
        is_active=True,
    )

    for availability in availabilities:
        start_dt = timezone.make_aware(datetime.combine(target_date, availability.start_time), tz)
        end_dt = timezone.make_aware(datetime.combine(target_date, availability.end_time), tz)
        intervals.append((start_dt, end_dt))

    exceptions = AvailabilityException.objects.filter(physician=physician, date=target_date)
    unavailable_intervals = []

    for exception in exceptions:
        start_dt = timezone.make_aware(datetime.combine(target_date, exception.start_time), tz)
        end_dt = timezone.make_aware(datetime.combine(target_date, exception.end_time), tz)

        if exception.exception_type == "extra_available":
            intervals.append((start_dt, end_dt))
        else:
            unavailable_intervals.append((start_dt, end_dt))

    intervals = _subtract_intervals(intervals, unavailable_intervals)

    bookings = Booking.objects.filter(
        consulting_physician=physician.user,
        scheduled_start__date=target_date,
        status__in=BLOCKING_BOOKING_STATUSES,
    ).values_list("scheduled_start", "scheduled_end")

    duration = timedelta(minutes=physician.consultation_duration_minutes)
    available_slots = []

    for interval_start, interval_end in intervals:
        cursor = interval_start
        while cursor + duration <= interval_end:
            slot_start = cursor
            slot_end = cursor + duration

            if slot_start <= now:
                cursor += duration
                continue

            overlapped = any(
                _has_overlap(slot_start, slot_end, booking_start, booking_end)
                for booking_start, booking_end in bookings
            )

            if not overlapped:
                available_slots.append((slot_start, slot_end))

            cursor += duration

    return available_slots


def validate_booking_slot(physician: PhysicianProfile, scheduled_start):
    if not physician.is_verified:
        return False, None, "physician_not_verified", "This physician is not verified yet."

    if not physician.accepts_bookings:
        return False, None, "physician_not_accepting_bookings", "This physician is not accepting bookings."

    if not physician.consultation_duration_minutes:
        return False, None, "slot_unavailable", "Consultation duration is not configured for this physician."

    if scheduled_start <= timezone.now():
        return False, None, "slot_unavailable", "Please choose a future consultation time."

    scheduled_end = scheduled_start + timedelta(minutes=physician.consultation_duration_minutes)

    available_slots = generate_available_slots(physician, timezone.localtime(scheduled_start).date())
    slot_found = any(
        slot_start == scheduled_start and slot_end == scheduled_end
        for slot_start, slot_end in available_slots
    )

    if not slot_found:
        return False, None, "slot_unavailable", "This consultation slot is no longer available."

    return True, scheduled_end, "", ""
