from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Basic pages
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('simple_register/', views.simple_register, name='simple_register'),
    path('enrollment/', views.enrollment, name='enrollment'),
    path('test_form/', views.test_form, name='test_form'),
    path('login/', auth_views.LoginView.as_view(template_name='blockchain_records/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='blockchain_records/logout.html'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Academic record management
    path('records/add/', views.add_record, name='add_record'),
    path('records/<int:record_id>/', views.record_detail, name='record_detail'),
    path('records/verify/', views.verify_record, name='verify_record'),
    path('students/<str:student_id>/records/', views.student_records, name='student_records'),
    path('students/search/', views.search_students, name='search_students'),

    # Course management
    path('courses/', views.course_list, name='course_list'),
    path('courses/add/', views.add_course, name='add_course'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/edit/', views.edit_course, name='edit_course'),

    # Blockchain explorer
    path('blockchain/explorer/', views.blockchain_explorer, name='blockchain_explorer'),

    # API endpoints
    path('api/blockchain/', views.BlockchainAPIView.as_view(), name='blockchain_api'),
]
