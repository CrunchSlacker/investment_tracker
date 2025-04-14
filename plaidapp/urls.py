from django.urls import path
from . import views
from .views import signup_view

urlpatterns = [
    path('', views.plaid_home, name='plaid_home'),
    path('create_link_token/', views.create_link_token, name='create_link_token'),
    path('exchange_public_token/', views.exchange_public_token, name='exchange_public_token'),
    path('link/', views.link_account_page, name='link_account_page'),

    path('signup/', signup_view, name='signup'),
]
