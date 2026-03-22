from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('booking/', views.calendar_view, name='calendar'),
    path('register/', views.student_register_view, name='student-register'),
    path('history/', views.history_view, name='history'),
    path('confirm-booking/', views.confirm_booking, name='confirm-booking'),
    path('admin/', views.admin_dashboard_view, name='admin-dashboard'),
    
    # API
    path('api/labs/', views.get_labs_list, name='labs-api'),
    path('api/labs/availability/', views.get_lab_availability, name='availability-api'),
    path('api/bookings/events/', views.get_booking_events, name='booking-events-api'),
    path('api/bookings/availability-events/', views.api_get_availability_events, name='availability-events-api'),
    path('api/bookings/list/', views.api_get_bookings_list, name='bookings-list-api'),
    path('api/bookings/create/', views.api_create_booking, name='booking-create-api'),
    path('api/bookings/update-status/', views.api_update_booking_status, name='booking-update-api'),
    path('api/bookings/resend-email/', views.api_resend_booking_email, name='booking-resend-email-api'),
    path('api/config/auto-approval/', views.api_get_auto_approval, name='get-auto-approval-api'),
    path('api/config/update-auto-approval/', views.api_update_auto_approval, name='update-auto-approval-api'),
    path('api/students/', views.api_get_students, name='students-list-api'),
    path('api/students/register/', views.api_register_student, name='students-register-api'),
    path('api/students/update/', views.api_update_student_status, name='students-update-api'),
    path('api/hygiene/report/', views.api_hygiene_report, name='hygiene-report-api'),
    path('api/hygiene/list/', views.api_get_hygiene_reports, name='hygiene-list-api'),
    path('api/export/bookings/', views.api_export_bookings_csv, name='export-bookings'),
]
