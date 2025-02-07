from django.contrib.auth import views as auth_views
from django.urls import path
from .views import *  # Import your views file
from .dashboard_views import *
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout_user'),
    path('signup/',signup,name = 'signup'),
    path('dashboard/', dashboard, name='dashboard'),
    
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('nurse-dashboard/', nurse_dashboard, name='nurse_dashboard'),
    path('patient-dashboard/', patient_dashboard, name='patient_dashboard'),
    path('doctor-dashboard/', doctor_dashboard, name='doctor_dashboard'),
    
    path('approve-doctors/', approve_doctors, name='approve_doctors'),
    
    path('approve-doctor/<int:doctor_id>/', approve_doctor, name='approve_doctor'),
    path('reject-doctor/<int:doctor_id>/', reject_doctor, name='reject_doctor'),

    path('approved-doctors/', approved_doctors, name='approved_doctors'),
    path('deactivate-doctor/<int:doctor_id>/', deactivate_doctor, name='deactivate_doctor'),
    
    path('patients/', view_patients, name='view_patients'),
    path('appointments/', view_appointments, name='view_appointments'),
    path('appointments/update/<int:appointment_id>/<str:new_status>/', update_appointment_status, name='update_appointment_status'),

    path("doctor-availability/", doctor_availability, name="doctor_availability"),

]

if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)