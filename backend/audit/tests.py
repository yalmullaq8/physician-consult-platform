from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from audit.models import AuditLog


class AuditLogAPITests(APITestCase):
	def setUp(self):
		self.client = APIClient()
		self.staff_user = User.objects.create_superuser(
			email="admin@example.com",
			password="pass1234",
			full_name="Admin User",
		)
		self.regular_user = User.objects.create_user(
			email="doctor@example.com",
			password="pass1234",
			full_name="Regular User",
		)

		self.payment_log = AuditLog.objects.create(
			actor=self.staff_user,
			action="payment_admin_mark_paid",
			object_type="payments.Payment",
			object_id="bulk",
			metadata={"updated": 1},
		)
		self.booking_log = AuditLog.objects.create(
			actor=self.staff_user,
			action="booking_admin_cancelled",
			object_type="bookings.Booking",
			object_id="bulk",
			metadata={"updated": 2},
		)

		old_time = timezone.now() - timedelta(days=2)
		AuditLog.objects.filter(pk=self.booking_log.pk).update(created_at=old_time)

	def test_non_staff_user_cannot_access_audit_logs(self):
		self.client.force_authenticate(self.regular_user)
		response = self.client.get("/api/audit/logs/", HTTP_HOST="localhost")

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_staff_user_can_list_audit_logs(self):
		self.client.force_authenticate(self.staff_user)
		response = self.client.get("/api/audit/logs/", HTTP_HOST="localhost")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(response.data["success"])
		self.assertEqual(response.data["data"]["count"], 2)
		self.assertEqual(len(response.data["data"]["results"]), 2)

	def test_staff_user_can_filter_audit_logs_by_action(self):
		self.client.force_authenticate(self.staff_user)
		response = self.client.get(
			"/api/audit/logs/",
			{"action": "payment_admin_mark_paid"},
			HTTP_HOST="localhost",
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["data"]["count"], 1)
		result = response.data["data"]["results"][0]
		self.assertEqual(result["action"], "payment_admin_mark_paid")
		self.assertEqual(result["object_type"], "payments.Payment")

	def test_staff_user_can_filter_audit_logs_by_date_range(self):
		self.client.force_authenticate(self.staff_user)
		created_from = (timezone.now() - timedelta(days=1)).date().isoformat()
		response = self.client.get(
			"/api/audit/logs/",
			{"created_from": created_from},
			HTTP_HOST="localhost",
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["data"]["count"], 1)
		result = response.data["data"]["results"][0]
		self.assertEqual(result["action"], "payment_admin_mark_paid")

	def test_staff_user_gets_400_for_invalid_date_filter(self):
		self.client.force_authenticate(self.staff_user)
		response = self.client.get(
			"/api/audit/logs/",
			{"created_from": "not-a-date"},
			HTTP_HOST="localhost",
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertFalse(response.data["success"])
		self.assertEqual(response.data["error"]["code"], "invalid_date_filter")

	def test_staff_user_can_export_csv(self):
		self.client.force_authenticate(self.staff_user)
		response = self.client.get(
			"/api/audit/logs/export/",
			{"action": "payment_admin_mark_paid"},
			HTTP_HOST="localhost",
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response["Content-Type"], "text/csv")
		self.assertIn("attachment; filename=\"audit_logs.csv\"", response["Content-Disposition"])
		body = response.content.decode("utf-8")
		self.assertIn("id,created_at,actor_email,action,object_type,object_id,metadata", body)
		self.assertIn("payment_admin_mark_paid", body)

	def test_non_staff_user_cannot_export_csv(self):
		self.client.force_authenticate(self.regular_user)
		response = self.client.get("/api/audit/logs/export/", HTTP_HOST="localhost")

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_staff_user_gets_400_for_invalid_date_filter_on_csv_export(self):
		self.client.force_authenticate(self.staff_user)
		response = self.client.get(
			"/api/audit/logs/export/",
			{"created_to": "bad-date"},
			HTTP_HOST="localhost",
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertFalse(response.data["success"])
		self.assertEqual(response.data["error"]["code"], "invalid_date_filter")
