from django.urls import path, include
from plaidapp import views
from django.contrib import admin

from plaidapp.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('plaid/', include('plaidapp.urls')),
    path('', views.home, name='home'),
    path('users/', include('users.urls')),
    path('', include('home.urls')),
    path('accounts/', include('accounts.urls')),
]

