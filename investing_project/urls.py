from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

from plaidapp.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('plaid/', include('plaidapp.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', home),
]
