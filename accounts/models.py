from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.TextField(blank=True, null=True)
    item_id = models.CharField(max_length=255, blank=True, null=True)  # optional
    
    def __str__(self):
        return self.user.username
