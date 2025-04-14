from django.db import models
from django.contrib.auth.models import User

class PlaidAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=255)
    item_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
from django.db import models

# Create your models here.
