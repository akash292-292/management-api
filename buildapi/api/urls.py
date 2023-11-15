from django.contrib import admin
from django.urls import path,include
from .views import *
urlpatterns = [
    path('',home),
    path('trigger_report/',trigger_report),
    path('get_report/',get_report),
]
