from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    class Action(models.TextChoices):
        UPLOAD = "upload", "Upload"
        VIEW = "view", "View"
        DOWNLOAD = "download", "Download"

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    document = models.ForeignKey("documents.Document", on_delete=models.PROTECT)
    action = models.CharField(max_length=20, choices=Action.choices)
    occurred_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ("-occurred_at", "-pk")
