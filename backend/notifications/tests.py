from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

from accounts.models import User
from audit.models import AuditLog
from notifications.admin import NotificationLogAdmin
from notifications.models import NotificationLog


class NotificationAdminActionsTests(TestCase):
	def setUp(self):
		self.site = AdminSite()
		self.factory = RequestFactory()
		self.admin_user = User.objects.create_superuser(
			email="admin@example.com",
			password="pass1234",
			full_name="Admin User",
		)
		self.recipient = User.objects.create_user(
			email="recipient@example.com",
			password="pass1234",
			full_name="Recipient User",
		)
		self.model_admin = NotificationLogAdmin(NotificationLog, self.site)

	def _admin_request(self):
		request = self.factory.post("/admin/notifications/notificationlog/")
		request.user = self.admin_user
		return request

	def _create_notification(self, *, status=NotificationLog.STATUS_PENDING, dedupe_key=None):
		return NotificationLog.objects.create(
			recipient=self.recipient,
			notification_type=NotificationLog.TYPE_PAYMENT_FAILED,
			status=status,
			subject="Test Subject",
			body="Test Body",
			dedupe_key=dedupe_key,
		)

	def test_mark_sent_updates_status_and_writes_audit_log(self):
		notification = self._create_notification(status=NotificationLog.STATUS_PENDING, dedupe_key="notif-1")
		request = self._admin_request()

		queryset = NotificationLog.objects.filter(pk=notification.pk)
		self.model_admin.mark_sent(request, queryset)

		notification.refresh_from_db()
		self.assertEqual(notification.status, NotificationLog.STATUS_SENT)
		self.assertIsNotNone(notification.sent_at)
		self.assertIsNone(notification.failed_at)

		audit = AuditLog.objects.get(action="notification_admin_mark_sent")
		self.assertEqual(audit.actor_id, self.admin_user.id)
		self.assertEqual(audit.object_type, "notifications.NotificationLog")
		self.assertEqual(audit.metadata["updated"], 1)
		self.assertEqual(audit.metadata["ids"], [notification.id])

	def test_reset_to_pending_clears_timestamps_and_writes_audit_log(self):
		notification = self._create_notification(status=NotificationLog.STATUS_FAILED, dedupe_key="notif-2")
		request = self._admin_request()

		queryset = NotificationLog.objects.filter(pk=notification.pk)
		self.model_admin.reset_to_pending(request, queryset)

		notification.refresh_from_db()
		self.assertEqual(notification.status, NotificationLog.STATUS_PENDING)
		self.assertIsNone(notification.sent_at)
		self.assertIsNone(notification.failed_at)

		audit = AuditLog.objects.get(action="notification_admin_reset_pending")
		self.assertEqual(audit.metadata["updated"], 1)
