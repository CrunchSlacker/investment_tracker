from django.contrib import admin
from .models import PlaidAccount

@admin.register(PlaidAccount)
class PlaidAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_id', 'access_token')
