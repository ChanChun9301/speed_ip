from django.urls import path
from .views import *

urlpatterns = [
    path('', speed_test_view, name='speed_test'),
    path('history/', history_view, name='speed_test_history'),
]