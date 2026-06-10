from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify


def _build_unique_slug(model_cls, source_value, current_pk=None):
	base_slug = slugify(source_value) or "item"
	slug_candidate = base_slug
	suffix = 2

	while model_cls.objects.filter(slug=slug_candidate).exclude(pk=current_pk).exists():
		slug_candidate = f"{base_slug}-{suffix}"
		suffix += 1

	return slug_candidate


class Specialty(models.Model):
	name = models.CharField(max_length=120, unique=True)
	slug = models.SlugField(max_length=140, unique=True, blank=True)
	description = models.TextField(blank=True)
	is_active = models.BooleanField(default=True)
	display_order = models.PositiveIntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["display_order", "name"]

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = _build_unique_slug(Specialty, self.name, self.pk)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.name


class PhysicianProfile(models.Model):
	user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="physician_profile")
	full_name = models.CharField(max_length=255)
	slug = models.SlugField(max_length=280, unique=True, blank=True)
	specialty = models.ForeignKey(Specialty, on_delete=models.PROTECT, related_name="physicians")
	subspecialty = models.CharField(max_length=255, blank=True)
	professional_title = models.CharField(max_length=255, blank=True)
	license_country = models.CharField(max_length=100, blank=True)
	hospital_or_clinic = models.CharField(max_length=255, blank=True)
	years_of_experience = models.PositiveIntegerField(default=0)
	bio = models.TextField(blank=True)
	consultation_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	consultation_duration_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
	profile_photo = models.FileField(upload_to="physician_photos/", blank=True)
	is_verified = models.BooleanField(default=False)
	is_featured = models.BooleanField(default=False)
	accepts_bookings = models.BooleanField(default=False)
	admin_notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["full_name"]

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = _build_unique_slug(PhysicianProfile, self.full_name, self.pk)
		super().save(*args, **kwargs)

	@property
	def can_receive_bookings(self):
		return (
			self.is_verified
			and self.accepts_bookings
			and self.consultation_price is not None
			and self.consultation_duration_minutes is not None
		)

	def __str__(self):
		return f"{self.full_name} ({self.user.email})"


class PhysicianAvailability(models.Model):
	WEEKDAY_CHOICES = (
		(0, "Monday"),
		(1, "Tuesday"),
		(2, "Wednesday"),
		(3, "Thursday"),
		(4, "Friday"),
		(5, "Saturday"),
		(6, "Sunday"),
	)

	physician = models.ForeignKey(PhysicianProfile, on_delete=models.CASCADE, related_name="availabilities")
	weekday = models.PositiveSmallIntegerField(choices=WEEKDAY_CHOICES)
	start_time = models.TimeField()
	end_time = models.TimeField()
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["physician", "weekday", "start_time"]

	def clean(self):
		if self.start_time >= self.end_time:
			raise ValidationError("Availability end time must be later than start time.")

		overlap_exists = PhysicianAvailability.objects.filter(
			physician=self.physician,
			weekday=self.weekday,
			is_active=True,
			start_time__lt=self.end_time,
			end_time__gt=self.start_time,
		).exclude(pk=self.pk).exists()

		if overlap_exists:
			raise ValidationError("This availability overlaps an existing active availability block.")

	def save(self, *args, **kwargs):
		self.full_clean()
		super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.physician.full_name} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"


class AvailabilityException(models.Model):
	EXCEPTION_TYPE_CHOICES = (
		("unavailable", "Unavailable"),
		("extra_available", "Extra Available"),
	)

	physician = models.ForeignKey(PhysicianProfile, on_delete=models.CASCADE, related_name="availability_exceptions")
	date = models.DateField()
	start_time = models.TimeField()
	end_time = models.TimeField()
	exception_type = models.CharField(max_length=20, choices=EXCEPTION_TYPE_CHOICES)
	reason = models.CharField(max_length=255, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["date", "start_time"]

	def clean(self):
		if self.start_time >= self.end_time:
			raise ValidationError("Exception end time must be later than start time.")

	def save(self, *args, **kwargs):
		self.full_clean()
		super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.physician.full_name} - {self.date} ({self.exception_type})"
