from django.db import models
from django.conf import settings

class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    credit = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.user + ',' + self.credit
