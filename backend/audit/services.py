from audit.models import AuditLog


def log_audit_event(*, actor=None, action: str, obj=None, object_type: str | None = None, object_id=None, metadata=None):
    if obj is not None:
        resolved_object_type = f"{obj._meta.app_label}.{obj.__class__.__name__}"
        resolved_object_id = str(obj.pk)
    else:
        resolved_object_type = object_type or "unknown"
        resolved_object_id = str(object_id or "unknown")

    return AuditLog.objects.create(
        actor=actor,
        action=action,
        object_type=resolved_object_type,
        object_id=resolved_object_id,
        metadata=metadata or {},
    )
