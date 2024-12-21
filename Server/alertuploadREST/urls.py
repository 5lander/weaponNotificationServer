from django.conf.urls import url, include
from rest_framework import routers
from . import views
from rest_framework.authtoken import views as rest_framework_views
from django.urls import path, include


urlpatterns = [
    # Alert POST
    path('images/', views.postAlert, name='postalert'),
    url(r'^get_auth_token/$', rest_framework_views.obtain_auth_token, name='get_auth_token'),
]