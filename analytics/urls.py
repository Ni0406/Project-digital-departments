# analytics/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage_view, name='homepage'),
    path('dashboard/<str:ticker_symbol>/', views.dashboard_view, name='dashboard'),
]