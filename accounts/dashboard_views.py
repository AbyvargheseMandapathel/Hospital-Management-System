from django.shortcuts import get_object_or_404, render,redirect
from django.contrib.auth.decorators import login_required
from .models import *  
from datetime import date
from django.contrib import messages
from .views import *

@login_required
@never_cache
def doctor_dashboard(request):
    if not hasattr(request.user, "doctor") or not request.user.doctor.is_approved:
        return render(request, "error.html", {"message": "Application not accepted by admin"})

    doctor = request.user.doctor

    total_appointments = Appointment.objects.filter(doctor=doctor).count()
    upcoming_appointments = Appointment.objects.filter(doctor=doctor, status="Confirmed").count()
    total_patients = Appointment.objects.filter(doctor=doctor).values("patient").distinct().count()

    recent_appointments = Appointment.objects.filter(doctor=doctor).order_by("-date", "-start_time")[:5]

    context = {
        "doctor": doctor,
        "total_appointments": total_appointments,
        "upcoming_appointments": upcoming_appointments,
        "total_patients": total_patients,
        "recent_appointments": recent_appointments,
    }

    return render(request, "doctor_dashboard.html", context)

@login_required
@never_cache
def nurse_dashboard(request):
    
    if not hasattr(request.user, "nurse") or not request.user.nurse.is_approved:
        return render(request, "error.html", {"message": "Application not accepted by admin"})
    
    """Displays the nurse's assigned appointments."""
    appointments = Appointment.objects.filter(nurse=request.user.nurse)
    return render(request, "nurse_dashboard.html", {"appointments": appointments})


# views.py
@user_passes_test(is_patient,login_url='login')
@never_cache
def patient_dashboard(request):
    # Ensure the user is a patient
    if not hasattr(request.user, 'patient'):
        messages.error(request, "You are not authorized to access this page.")
        return redirect("login")

    patient = request.user.patient
    now = timezone.now().date()

    # Next Appointment (closest upcoming appointment)
    next_appointment = Appointment.objects.filter(
        patient=patient,
        date__gte=now
    ).order_by('date', 'start_time').first()

    # Upcoming Appointments (all future appointments)
    upcoming_appointments = Appointment.objects.filter(
        patient=patient,
        date__gte=now
    ).order_by('date', 'start_time')

    context = {
        'next_appointment': next_appointment,
        'upcoming_appointments': upcoming_appointments,
    }
    return render(request, 'patient_dashboard.html', context)

@login_required

def appointment_detail(request, appointment_id):
    # Fetch the appointment object
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Authorization logic
    if hasattr(request.user, 'patient') and request.user.patient == appointment.patient:
        authorized = True
    elif hasattr(request.user, 'doctor') and request.user.doctor == appointment.doctor:
        authorized = True
    elif hasattr(request.user, 'nurse') and request.user.nurse == appointment.nurse:
        authorized = True
    elif request.user.is_superuser:
        authorized = True
    else:
        messages.error(request, "You are not authorized to access this page.")
        return redirect("login")

    context = {
        'appointment': appointment
    }
    return render(request, 'appointment_detail.html', context)


@login_required
def cancel_appointment(request, appointment_id):
    # Ensure the user is a patient and owns the appointment
    if not hasattr(request.user, 'patient'):
        messages.error(request, "You are not authorized to access this page.")
        return redirect("login")

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient=request.user.patient
    )

    # Check if the appointment can be canceled
    if appointment.status == 'Canceled':
        messages.warning(request, "This appointment is already canceled.")
    elif appointment.status not in ['Pending', 'Confirmed']:
        messages.error(request, "This appointment cannot be canceled.")
    else:
        # Cancel the appointment
        appointment.status = 'Canceled'
        appointment.save()
        messages.success(request, "Appointment canceled successfully.")

    return redirect('patient_dashboard')


@login_required
def vital_records_view(request, appointment_id):
    """
    View for doctors and nurses to see vital records of an appointment.
    Only the assigned nurse and doctor can view the vitals.
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Ensure that only the assigned doctor or nurse can view this
    if request.user != appointment.doctor.user and request.user != appointment.nurse.user:
        return render(request, "403.html", status=403)  # Forbidden access
    
    vitals = appointment.vitals  # Access related vitals using related_name

    context = {
        "appointment": appointment,
        "vitals": vitals,
    }
    return render(request, "vital_records.html", context)
