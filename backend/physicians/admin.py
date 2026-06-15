from django.contrib import admin

from audit.services import log_audit_event

from .models import AvailabilityException, PhysicianAvailability, PhysicianProfile, Specialty


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
	list_display = ("name", "slug", "is_active", "display_order", "updated_at")
	list_filter = ("is_active",)
	search_fields = ("name",)
	ordering = ("display_order", "name")


@admin.register(PhysicianProfile)
class PhysicianProfileAdmin(admin.ModelAdmin):
	list_display = (
		"full_name",
		"specialties_list",
		"license_country",
		"consultation_price",
		"consultation_duration_minutes",
		"is_verified",
		"accepts_bookings",
		"is_featured",
		"created_at",
	)
	list_filter = ("specialties", "is_verified", "is_featured", "accepts_bookings", "license_country")
	search_fields = ("full_name", "user__email", "hospital_or_clinic")
	autocomplete_fields = ("user", "specialties")
	readonly_fields = ("created_at", "updated_at", "can_receive_bookings")
	actions = (
		"mark_verified",
		"mark_unverified",
		"enable_bookings",
		"disable_bookings",
		"mark_featured",
		"unmark_featured",
	)

	fieldsets = (
		(None, {"fields": ("user", "full_name", "slug", "specialties", "subspecialty", "professional_title")}),
		(
			"Professional Details",
			{
				"fields": (
					"license_country",
					"hospital_or_clinic",
					"years_of_experience",
					"bio",
					"profile_photo",
				)
			},
		),
		(
			"Consultation Settings",
			{
				"fields": (
					"consultation_price",
					"consultation_duration_minutes",
					"is_verified",
					"is_featured",
					"accepts_bookings",
					"can_receive_bookings",
				)
			},
		),
		("Admin", {"fields": ("admin_notes", "created_at", "updated_at")}),
	)

	@admin.display(description="Specialties")
	def specialties_list(self, obj):
		return ", ".join(obj.specialties.values_list("name", flat=True))

	def _log_bulk_action(self, request, queryset, action):
		selected_ids = list(queryset.values_list("id", flat=True))
		log_audit_event(
			actor=request.user,
			action=action,
			object_type="physicians.PhysicianProfile",
			object_id="bulk",
			metadata={"ids": selected_ids, "count": len(selected_ids)},
		)

	@admin.action(description="Mark selected physicians as verified")
	def mark_verified(self, request, queryset):
		queryset.update(is_verified=True)
		self._log_bulk_action(request, queryset, "physician_mark_verified")

	@admin.action(description="Mark selected physicians as unverified")
	def mark_unverified(self, request, queryset):
		queryset.update(is_verified=False)
		self._log_bulk_action(request, queryset, "physician_mark_unverified")

	@admin.action(description="Enable bookings for selected physicians")
	def enable_bookings(self, request, queryset):
		queryset.update(accepts_bookings=True)
		self._log_bulk_action(request, queryset, "physician_enable_bookings")

	@admin.action(description="Disable bookings for selected physicians")
	def disable_bookings(self, request, queryset):
		queryset.update(accepts_bookings=False)
		self._log_bulk_action(request, queryset, "physician_disable_bookings")

	@admin.action(description="Feature selected physicians")
	def mark_featured(self, request, queryset):
		queryset.update(is_featured=True)
		self._log_bulk_action(request, queryset, "physician_mark_featured")

	@admin.action(description="Unfeature selected physicians")
	def unmark_featured(self, request, queryset):
		queryset.update(is_featured=False)
		self._log_bulk_action(request, queryset, "physician_unmark_featured")


@admin.register(PhysicianAvailability)
class PhysicianAvailabilityAdmin(admin.ModelAdmin):
	list_display = ("physician", "weekday", "start_time", "end_time", "is_active")
	list_filter = ("weekday", "is_active")
	search_fields = ("physician__full_name", "physician__user__email")
	autocomplete_fields = ("physician",)


@admin.register(AvailabilityException)
class AvailabilityExceptionAdmin(admin.ModelAdmin):
	list_display = ("physician", "date", "start_time", "end_time", "exception_type")
	list_filter = ("exception_type", "date")
	search_fields = ("physician__full_name", "physician__user__email", "reason")
	autocomplete_fields = ("physician",)
