from django.db import models
from django.contrib.auth.models import User

class PlaidAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    access_token = models.TextField()
    item_id = models.CharField(max_length=255)
    institution_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.item_id}"



