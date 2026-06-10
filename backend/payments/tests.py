from datetime import timedelta
from decimal import Decimal

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase
from django.utils import timezone

from accounts.models import User
from audit.models import AuditLog
from bookings.models import Booking
from payments.admin import PaymentAdmin
from payments.models import Payment


class PaymentAdminActionsTests(TestCase):
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
		self.model_admin = PaymentAdmin(Payment, self.site)

	def _admin_request(self):
		request = self.factory.post("/admin/payments/payment/")
		request.user = self.admin_user
		return request

	def _create_booking(self, reference, status):
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

	def _create_payment(self, booking, status):
		return Payment.objects.create(
			booking=booking,
			amount=Decimal("30.00"),
			currency="KWD",
			status=status,
		)

	def test_mark_paid_confirms_pending_booking_and_writes_audit_log(self):
		booking = self._create_booking("BK-PAY-001", Booking.STATUS_PENDING_PAYMENT)
		payment = self._create_payment(booking, Payment.STATUS_PENDING)
		request = self._admin_request()

		queryset = Payment.objects.filter(pk=payment.pk)
		self.model_admin.mark_paid(request, queryset)

		payment.refresh_from_db()
		booking.refresh_from_db()
		self.assertEqual(payment.status, Payment.STATUS_PAID)
		self.assertIsNotNone(payment.paid_at)
		self.assertEqual(booking.status, Booking.STATUS_CONFIRMED)

		audit = AuditLog.objects.get(action="payment_admin_mark_paid")
		self.assertEqual(audit.actor_id, self.admin_user.id)
		self.assertEqual(audit.object_type, "payments.Payment")
		self.assertEqual(audit.metadata["count"], 1)
		self.assertEqual(audit.metadata["updated"], 1)
		self.assertEqual(audit.metadata["ids"], [payment.id])
		self.assertEqual(audit.metadata["skipped"], [])

	def test_mark_refunded_skips_non_paid_and_writes_skip_metadata(self):
		booking = self._create_booking("BK-PAY-002", Booking.STATUS_PENDING_PAYMENT)
		payment = self._create_payment(booking, Payment.STATUS_PENDING)
		request = self._admin_request()

		queryset = Payment.objects.filter(pk=payment.pk)
		self.model_admin.mark_refunded(request, queryset)

		payment.refresh_from_db()
		booking.refresh_from_db()
		self.assertEqual(payment.status, Payment.STATUS_PENDING)
		self.assertEqual(booking.status, Booking.STATUS_PENDING_PAYMENT)

		audit = AuditLog.objects.get(action="payment_admin_mark_refunded")
		self.assertEqual(audit.metadata["updated"], 0)
		self.assertEqual(audit.metadata["skipped"], [payment.id])
