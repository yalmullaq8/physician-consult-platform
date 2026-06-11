import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

print("DEBUG CELERY_BROKER_URL:", os.environ.get("CELERY_BROKER_URL"))
print("DEBUG REDIS_URL:", os.environ.get("REDIS_URL"))
