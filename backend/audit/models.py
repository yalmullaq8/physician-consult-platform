from django.db import models


class AuditLog(models.Model):
	actor = models.ForeignKey(
		"accounts.User",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="audit_logs",
	)
	action = models.CharField(max_length=120)
	object_type = models.CharField(max_length=120)
	object_id = models.CharField(max_length=120)
	metadata = models.JSONField(default=dict, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["action", "created_at"]),
			models.Index(fields=["object_type", "object_id"]),
		]

	def __str__(self):
		return f"{self.action} on {self.object_type}:{self.object_id}"
