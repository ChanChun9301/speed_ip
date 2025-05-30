from django.urls import path
from .views import *

urlpatterns = [
    path('', first_visit, name='first_visit'),
    path('home/', index, name='home'),
    path('speed_test/', speed_test_view, name='speed_test'),
    path('history/', history_view, name='speed_test_history'),
    path('search_history_view/', search_history_view, name='search_history_view'),
    path('api/commands/', get_commands, name='get_commands'),
    path('traffic/', traffic_logs, name='traffic_logs'),
    path('list/', com_list, name='com_list'),
    path('save_search/', save_search, name='save_search'),

    path('auth/', auth_view, name='auth'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),

    path('speed-test-results/', speed_test_results_list, name='speed_test_results_list'),
    path('speed-test-results/<int:result_id>/', speed_test_results_detail, name='speed_test_results_detail'),

]