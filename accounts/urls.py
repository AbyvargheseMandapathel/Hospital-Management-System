from django.contrib.auth import views as auth_views
from django.urls import path
from .views import *  # Import your views file
from .dashboard_views import *
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('', home, name='home'),
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

    path('doctor/availability/', doctor_availability, name='doctor_availability'),
    path('doctor/availability/delete/<int:availability_id>/', delete_availability, name='delete_availability'),
    path('appointment/<int:appointment_id>/status/<str:new_status>/', update_appointment_status, name='update_appointment_status'),
    path('doctor_appointments/', doctor_appointments_view, name='doctor_appointment'),
    path('appointments/<str:appointment_id>/update/', update_appointment, name="update_appointment"),
    path('password-reset/', password_reset_request, name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', password_reset_confirm, name='password_reset_confirm'),
    path('book_appointment/', book_appointment_flow, name='book_appointment_flow'),
    path('appointment/<str:appointment_id>/view_comments/', view_doctor_comments, name="view_doctor_comments"),
    
    path("appointment-status/", appointment_status, name="appointment_status"),
    path("patients/doctors/", doctors_view_patient, name="doctors_view_patient"),
    
    path('appointment/<int:appointment_id>/', appointment_detail, name='appointment_detail'),
    path('appointment/cancel/<int:appointment_id>/', cancel_appointment, name='cancel_appointment'),
    
    path('my-appointments/', patient_appointments_view, name='patient_appointments'),
    
    path("predict-page/", predict_page, name="predict_page"),
    path("predict/", predict_disease, name="predict"),
    
    path('doc-appointments/', doctor_appointments_view, name='doctor_appointments_view'),
    path('consulted-patients/', consulted_patients_list, name='consulted_patients'),
    
    path('patient/<int:patient_id>/', patient_detail, name='patient_detail'),
    
    path("appointment/<int:appointment_id>/add-vitals/", add_vitals, name="add_vitals"),
    path("nurse/appointments/", view_appointments_nurse, name="view_appointments_nurse"),
    
    path("vitals/<int:appointment_id>/", vital_records_view, name="vital_records"),
    
    path("my-feedback/", user_feedback_list, name="user_feedback_list"),
    path("submit/", submit_feedback, name="submit_feedback"),
    path("list/", feedback_list, name="feedback_list"),
    path("reply/<int:feedback_id>/", admin_reply_feedback, name="admin_reply_feedback"),

]


if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)