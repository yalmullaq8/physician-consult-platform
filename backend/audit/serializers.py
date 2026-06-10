from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
	actor_email = serializers.EmailField(source="actor.email", allow_null=True)

	class Meta:
		model = AuditLog
		fields = (
			"id",
			"actor_email",
			"action",
			"object_type",
			"object_id",
			"metadata",
			"created_at",
		)
