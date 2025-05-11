from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True)
    eth_address = models.CharField(max_length=42, blank=True, null=True)
    eth_index = models.PositiveIntegerField(blank=True, null=True, unique=True)
