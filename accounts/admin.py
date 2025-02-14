from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Profile)
admin.site.register(Nurse)
admin.site.register(Doctor)
admin.site.register(Patient)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('appointment_id', 'doctor', 'patient', 'date', 'start_time', 'end_time', 'status')
    search_fields = ('appointment_id', 'doctor__user__last_name', 'patient__user__first_name')

admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(DoctorAvailability)
admin.site.register(VitalsRecord)

