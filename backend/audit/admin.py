from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
	list_display = ("action", "actor", "object_type", "object_id", "created_at")
	list_filter = ("action", "object_type", "created_at")
	search_fields = ("action", "object_type", "object_id", "actor__email")
	readonly_fields = ("actor", "action", "object_type", "object_id", "metadata", "created_at")
	date_hierarchy = "created_at"
	list_select_related = ("actor",)
