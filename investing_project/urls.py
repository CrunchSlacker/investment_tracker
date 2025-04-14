from django.urls import path, include
from plaidapp import views
from django.contrib import admin

# from plaidapp.views import home
from home.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('plaid/', include('plaidapp.urls')),
    path('', home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
]

