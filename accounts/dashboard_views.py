from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from .models import *  
from datetime import date
from django.contrib import messages


@login_required
def doctor_dashboard(request):
    if not hasattr(request.user, 'doctor') or not request.user.doctor.is_approved:
        return render(request, 'error.html', {'message': 'Application not accepted by admin'})

    return render(request, 'doctor_dashboard.html')

@login_required
def nurse_dashboard(request):
    return render(request, 'nurse_dashboard.html')


@login_required
def patient_dashboard(request):
    # Check if the logged in user has a patient profile
    if not hasattr(request.user, 'patient'):
        messages.error(request, "You are not authorized to access this page. Please log in as a patient.")
        return redirect("login")  # Change "login" to the appropriate URL name if needed

    # Retrieve all appointments for the logged in patient
    appointments = Appointment.objects.filter(patient=request.user.patient).order_by('-date', 'start_time')
    
    if not appointments.exists():
        messages.info(request, "You have no appointments scheduled.")

    return render(request, 'patient_dashboard.html', {'appointments': appointments})

