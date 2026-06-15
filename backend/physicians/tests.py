from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import User

from .models import AvailabilityException, PhysicianAvailability, PhysicianProfile, Specialty


class MyAvailabilityAPITests(APITestCase):
	def setUp(self):
		self.client = APIClient()
		self.specialty = Specialty.objects.create(name="Cardiology")

		self.physician_user = User.objects.create_user(
			email="physician@example.com",
			password="pass1234",
			full_name="Physician User",
		)
		self.non_physician_user = User.objects.create_user(
			email="regular@example.com",
			password="pass1234",
			full_name="Regular User",
		)

		self.profile = PhysicianProfile.objects.create(
			user=self.physician_user,
			full_name="Dr. Physician",
			license_country="KW",
			consultation_price="20.00",
			consultation_duration_minutes=30,
			is_verified=True,
			accepts_bookings=True,
		)
		self.profile.specialties.set([self.specialty])

	def test_non_physician_user_cannot_access_my_availability(self):
		self.client.force_authenticate(self.non_physician_user)
		response = self.client.get("/api/me/availability/", HTTP_HOST="localhost")

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_physician_can_create_and_list_availability_blocks(self):
		self.client.force_authenticate(self.physician_user)
		create_response = self.client.post(
			"/api/me/availability/blocks/",
			{"weekday": 1, "start_time": "09:00", "end_time": "10:00", "is_active": True},
			format="json",
			HTTP_HOST="localhost",
		)

		self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
		self.assertTrue(create_response.data["success"])

		list_response = self.client.get("/api/me/availability/", HTTP_HOST="localhost")
		self.assertEqual(list_response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(list_response.data["data"]["blocks"]), 1)
		self.assertEqual(list_response.data["data"]["blocks"][0]["weekday"], 1)

	def test_overlap_block_creation_returns_400(self):
		PhysicianAvailability.objects.create(
			physician=self.profile,
			weekday=2,
			start_time="09:00",
			end_time="10:00",
		)
		self.client.force_authenticate(self.physician_user)

		response = self.client.post(
			"/api/me/availability/blocks/",
			{"weekday": 2, "start_time": "09:30", "end_time": "10:30", "is_active": True},
			format="json",
			HTTP_HOST="localhost",
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertFalse(response.data["success"])

	def test_physician_can_create_and_delete_exception(self):
		self.client.force_authenticate(self.physician_user)
		create_response = self.client.post(
			"/api/me/availability/exceptions/",
			{
				"date": "2026-12-01",
				"start_time": "10:00",
				"end_time": "11:00",
				"exception_type": "unavailable",
				"reason": "Conference",
			},
			format="json",
			HTTP_HOST="localhost",
		)

		self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
		exception_id = create_response.data["data"]["id"]

		delete_response = self.client.delete(
			f"/api/me/availability/exceptions/{exception_id}/",
			HTTP_HOST="localhost",
		)
		self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
		self.assertEqual(AvailabilityException.objects.count(), 0)

	def test_physician_can_update_availability_block(self):
		self.client.force_authenticate(self.physician_user)
		block = PhysicianAvailability.objects.create(
			physician=self.profile,
			weekday=1,
			start_time="09:00",
			end_time="10:00",
		)

		response = self.client.patch(
			f"/api/me/availability/blocks/{block.id}/",
			{"start_time": "10:00", "end_time": "11:00"},
			format="json",
			HTTP_HOST="localhost",
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(response.data["success"])
		block.refresh_from_db()
		self.assertEqual(str(block.start_time)[:5], "10:00")
		self.assertEqual(str(block.end_time)[:5], "11:00")

	def test_physician_can_update_availability_exception(self):
		self.client.force_authenticate(self.physician_user)
		exception = AvailabilityException.objects.create(
			physician=self.profile,
			date="2026-12-02",
			start_time="10:00",
			end_time="11:00",
			exception_type="unavailable",
			reason="Busy",
		)

		response = self.client.patch(
			f"/api/me/availability/exceptions/{exception.id}/",
			{"exception_type": "extra_available", "reason": "Opened extra session"},
			format="json",
			HTTP_HOST="localhost",
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(response.data["success"])
		exception.refresh_from_db()
		self.assertEqual(exception.exception_type, "extra_available")
		self.assertEqual(exception.reason, "Opened extra session")


class PublicPhysicianAPITests(APITestCase):
	def setUp(self):
		self.client = APIClient()
		self.cardiology = Specialty.objects.create(name="Cardiology")
		self.neurology = Specialty.objects.create(name="Neurology")
		self.dermatology = Specialty.objects.create(name="Dermatology")

		self.user = User.objects.create_user(
			email="public-physician@example.com",
			password="pass1234",
			full_name="Public Physician",
		)
		self.profile = PhysicianProfile.objects.create(
			user=self.user,
			full_name="Dr. Multi Specialty",
			license_country="KW",
			consultation_price="30.00",
			consultation_duration_minutes=25,
			is_verified=True,
			accepts_bookings=True,
		)
		self.profile.specialties.set([self.cardiology, self.neurology])

		self.other_user = User.objects.create_user(
			email="other-physician@example.com",
			password="pass1234",
			full_name="Other Physician",
		)
		self.other_profile = PhysicianProfile.objects.create(
			user=self.other_user,
			full_name="Dr. Skin Expert",
			license_country="KW",
			consultation_price="25.00",
			consultation_duration_minutes=20,
			is_verified=True,
			accepts_bookings=True,
		)
		self.other_profile.specialties.set([self.dermatology])

	def test_public_physician_list_returns_specialties_array(self):
		response = self.client.get("/api/physicians/", HTTP_HOST="localhost")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(response.data["success"])
		first_result = response.data["data"][0]
		self.assertIn("specialties", first_result)
		self.assertNotIn("specialty", first_result)
		self.assertGreaterEqual(len(first_result["specialties"]), 1)

	def test_public_physician_detail_returns_specialties_array(self):
		response = self.client.get(f"/api/physicians/{self.profile.slug}/", HTTP_HOST="localhost")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(response.data["success"])
		self.assertEqual(
			[item["slug"] for item in response.data["data"]["specialties"]],
			[self.cardiology.slug, self.neurology.slug],
		)

	def test_public_physician_list_filters_by_single_specialty_param(self):
		response = self.client.get(
			f"/api/physicians/?specialty={self.neurology.slug}",
			HTTP_HOST="localhost",
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(response.data["success"])
		results = response.data["data"]
		self.assertEqual(len(results), 1)
		self.assertEqual(results[0]["slug"], self.profile.slug)
