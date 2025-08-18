from django.urls import re_path, include, path
from rest_framework import routers
from . import views
from rest_framework.authtoken import views as rest_framework_views

urlpatterns = [
    # Alert POST
    path('images/', views.postAlert, name='postalert'),
    re_path(r'^get_auth_token/$', rest_framework_views.obtain_auth_token, name='get_auth_token'),
]