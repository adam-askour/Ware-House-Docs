from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    scanner_code = models.CharField(max_length=64, unique=True, null=True, blank=True)

    def __str__(self) -> str:
        return self.get_full_name() or self.username
