from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name='home'),
    path('speed_test/', speed_test_view, name='speed_test'),
    path('history/', history_view, name='speed_test_history'),

    path('auth/', auth_view, name='auth'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),

    path('speed-test-results/', speed_test_results_list, name='speed_test_results_list'),
    path('speed-test-results/<int:result_id>/', speed_test_results_detail, name='speed_test_results_detail'),
    path('search-queries/', search_query_list, name='search_query_list'),
    path('search/', search_interface, name='search_interface'),
    path('exploit-db-dorks/', exploit_db_dork_list, name='exploit_db_dork_list'),
    path('exploit-db-dorks/<int:dork_id>/', exploit_db_dork_detail, name='exploit_db_dork_detail'),
]