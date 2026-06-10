from django.urls import path

from .views import AuditLogCSVExportView, AuditLogListView

urlpatterns = [
    path("audit/logs/", AuditLogListView.as_view(), name="audit-log-list"),
    path("audit/logs/export/", AuditLogCSVExportView.as_view(), name="audit-log-export"),
]
