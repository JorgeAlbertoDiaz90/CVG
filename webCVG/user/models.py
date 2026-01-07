from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    ide = models.IntegerField(null=True, blank=True)
    idvend = models.CharField(max_length=5, null=True, blank=True)