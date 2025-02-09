from django.shortcuts import get_object_or_404, render,redirect
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


# views.py
@login_required
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
    # Ensure the user is a patient and owns the appointment
    if not hasattr(request.user, 'patient'):
        messages.error(request, "You are not authorized to access this page.")
        return redirect("login")

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient=request.user.patient
    )

    context = {
        'appointment': appointment,
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

