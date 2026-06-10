from datetime import timedelta

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase
from django.utils import timezone

from accounts.models import User
from audit.models import AuditLog
from bookings.admin import BookingAdmin
from bookings.models import Booking


class BookingAdminActionsTests(TestCase):
	def setUp(self):
		self.site = AdminSite()
		self.factory = RequestFactory()
		self.admin_user = User.objects.create_superuser(
			email="admin@example.com",
			password="pass1234",
			full_name="Admin User",
		)
		self.requesting = User.objects.create_user(
			email="requester@example.com",
			password="pass1234",
			full_name="Requester User",
		)
		self.consulting = User.objects.create_user(
			email="consultant@example.com",
			password="pass1234",
			full_name="Consulting User",
		)
		self.model_admin = BookingAdmin(Booking, self.site)

	def _admin_request(self):
		request = self.factory.post("/admin/bookings/booking/")
		request.user = self.admin_user
		return request

	def _create_booking(self, reference, status=Booking.STATUS_PENDING_PAYMENT):
		start = timezone.now() + timedelta(days=1)
		end = start + timedelta(minutes=30)
		return Booking.objects.create(
			booking_reference=reference,
			requesting_physician=self.requesting,
			consulting_physician=self.consulting,
			scheduled_start=start,
			scheduled_end=end,
			status=status,
			case_summary="Summary",
		)

	def test_cancel_bookings_sets_cancel_fields_and_writes_audit_log(self):
		booking = self._create_booking("BK-ADMIN-001")
		request = self._admin_request()

		queryset = Booking.objects.filter(pk=booking.pk)
		self.model_admin.cancel_bookings(request, queryset)

		booking.refresh_from_db()
		self.assertEqual(booking.status, Booking.STATUS_CANCELLED)
		self.assertEqual(booking.cancellation_reason, "Cancelled by admin")
		self.assertEqual(booking.cancelled_by_id, self.admin_user.id)
		self.assertIsNotNone(booking.cancelled_at)

		audit = AuditLog.objects.get(action="booking_admin_cancelled")
		self.assertEqual(audit.actor_id, self.admin_user.id)
		self.assertEqual(audit.object_type, "bookings.Booking")
		self.assertEqual(audit.object_id, "bulk")
		self.assertEqual(audit.metadata["count"], 1)
		self.assertEqual(audit.metadata["updated"], 1)
		self.assertEqual(audit.metadata["ids"], [booking.id])
