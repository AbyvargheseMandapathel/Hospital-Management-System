from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib import messages
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from .utils import send_status_email
from django.db.models import Q
from datetime import date
from .forms import *
from django.utils.timezone import datetime, timedelta
from django.http import HttpResponse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from .forms import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import joblib  # Import joblib for saving models
from django.db.models import Count


# Create your views here.

def home(request):
    return render(request, 'home.html')

User = get_user_model()  # Fetch the custom user model if defined
def signup(request):
    if request.method == "POST":
        # Collect form data
        username = request.POST.get('username')
        print(username)
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        place = request.POST.get('place')
        dob = request.POST.get('dob')
        user_type = request.POST.get('user_type')

        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('signup')

        # Check if passwords match  
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")
        
        
        try:
            # Create the user
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email,
                place=place,
                dob=dob,
                user_type=user_type,
            )

            # Handle user-type specific fields
            if user_type == 'nurse':
                nurse_phone = request.POST.get('nurse_phone')
                shift = request.POST.get('shift')
                if not nurse_phone or not shift:
                    messages.error(request, "Phone number and shift are required for nurses.")
                    user.delete()
                    return redirect('signup')

                Nurse.objects.create(
                    user=user,
                    phone_number=nurse_phone,
                    shift=shift,
                )
                print("Nurse details saved.")

            elif user_type == 'doctor':
                print(Doctor)
                doctor_phone = request.POST.get('doctor_phone')
                # print(doctor_phone)
                specialization = request.POST.get('specialization')
                experience = request.POST.get('experience')
                certificate_file = request.FILES.get('certificate_file')

                if  not specialization or not experience:
                    messages.error(request, "Phone number, specialization, and experience are required for doctors.")
                    user.delete()
                    return redirect('signup')

                Doctor.objects.create(
                    user=user,
                    specialization=specialization,
                    experience=experience,
                    phone_number=doctor_phone,
                    certificate_files=certificate_file
                )
                print("Doctor details saved.")

            elif user_type == 'patient':
                patient_phone = request.POST.get('patient_phone')
                print(patient_phone)

                if not patient_phone:
                    messages.error(request, "Phone number is required for patients.")
                    user.delete()
                    return redirect('signup')

                Patient.objects.create(user=user, phone_number=patient_phone)
                print("Patient details saved.")

            messages.success(request, "Signup successful! Please log in.")
            return redirect('login')

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('signup')

    # Render the signup form for GET requests
    return render(request, 'signup.html')

def login_user(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('login')

    return render(request, 'login.html')


@login_required
def dashboard(request):

    if request.user.user_type == 'admin':
        return redirect('admin_dashboard')
    if request.user.user_type == 'nurse':
        return redirect('nurse_dashboard')
    if request.user.user_type == 'patient':
        return redirect('patient_dashboard')
    if request.user.user_type == 'doctor':
        return redirect('doctor_dashboard')

    return redirect('login')

def logout_user(request):
    logout(request)
    return redirect('login')

def password_reset_request(request):
    if request.method == "POST":
        email = request.POST.get("email")
        user = User.objects.filter(email=email).first()

        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"http://127.0.0.1:8000/password-reset-confirm/{uid}/{token}/"

            # Send email
            send_mail(
                subject="Password Reset Request",
                message=f"Click the link below to reset your password:\n{reset_url}",
                from_email="your-email@gmail.com",
                recipient_list=[user.email],
                fail_silently=False,
            )

            messages.success(request, "A password reset link has been sent to your email.")
        else:
            messages.error(request, "No account found with this email.")

        return redirect("password_reset")

    return render(request, "password_reset.html")


def password_reset_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError):
        messages.error(request, "Invalid password reset link.")
        return redirect("password_reset")

    if not default_token_generator.check_token(user, token):
        messages.error(request, "Password reset link has expired.")
        return redirect("password_reset")

    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password == confirm_password:
            user.set_password(new_password)
            user.save()
            messages.success(request, "Your password has been successfully reset.")
            return redirect("login")
        else:
            messages.error(request, "Passwords do not match.")

    return render(request, "password_reset_confirm.html", {"uidb64": uidb64, "token": token})

@login_required
def admin_dashboard(request):
    # Fetch total counts
    total_doctors = Doctor.objects.count()
    total_patients = Patient.objects.count()
    total_appointments = Appointment.objects.count()

    # Fetch recent appointments (e.g., last 5 appointments)
    recent_appointments = Appointment.objects.all().order_by('-date')[:5]


    # Prepare context for rendering
    context = {
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'total_appointments': total_appointments,
        'recent_appointments': recent_appointments,
    }
    
    print(context)

    return render(request, 'admin_dashboard.html', context)


# Helper function to check if user is an admin or teacher (modify accordingly)
def is_admin(user):
    return user.is_authenticated and user.user_type in ['admin']

def is_patient(user):
    return user.is_authenticated and user.user_type in ['patient']

def is_doctor(user):
    return user.is_authenticated and hasattr(user, 'doctor') and user.doctor.is_approved

def is_doctor_admin(user):
    return user.is_authenticated and hasattr(user, 'doctor') and user.doctor.is_approved or user.user_type in ['admin']


@user_passes_test(is_admin, login_url='login')
def approve_doctors(request):
    """ View to fetch and display unapproved doctors """

    doctors = Doctor.objects.filter(is_approved=False).select_related('user')
    print(doctors)
    return render(request, 'approve_doctors.html', {'doctors': doctors})

@user_passes_test(is_admin, login_url='login')
def approve_doctor(request, doctor_id):
    """ View to approve a doctor and send email notification """
    try:
        doctor = get_object_or_404(Doctor, id=doctor_id, is_approved=False)
        doctor.is_approved = True  # Approve doctor
        doctor.status = 'Approved'
        doctor.save()

        # Send approval email
        subject = "Your Doctor Application Has Been Approved"
        message = f"Dear {doctor.user.first_name},\n\nYour application as a doctor has been approved. You can now access the platform as a verified doctor.\n\nBest regards,\nAdmin Team"
        send_status_email(doctor.user.email, subject, message)

        messages.success(request, f"Doctor {doctor.user.username} has been approved successfully.")
    except Profile.DoesNotExist:
        messages.error(request, "Doctor not found or already approved.")
    
    return redirect('approve_doctors')

@user_passes_test(is_admin, login_url='login')
def reject_doctor(request, doctor_id):
    """ View to reject and delete an unapproved doctor and send email notification """
    try:
        doctor = Profile.objects.get(id=doctor_id, user_type='doctor', is_approved=False)
        
        # Send rejection email before deleting
        subject = "Your Doctor Application Has Been Rejected"
        message = f"Dear {doctor.user.first_name},\n\nWe regret to inform you that your application as a doctor has been rejected. If you have any questions, please contact our support team.\n\nBest regards,\nAdmin Team"
        send_status_email(doctor.user.email, subject, message)
        doctor.status = 'Rejected'
        doctor.save()
        messages.success(request, f"Doctor {doctor.user.username} has been rejected and removed.")
    except Profile.DoesNotExist:
        messages.error(request, "Doctor not found or already rejected.")
    
    return redirect('approve_doctors')


@user_passes_test(is_admin, login_url='login')
def approved_doctors(request):
    """ View to list all approved doctors with filtering options """
    doctors = Doctor.objects.filter(is_approved=True).select_related('user')

    # Get filter values from request
    name_query = request.GET.get('name', '').strip()
    specialization_query = request.GET.get('specialization', '').strip()

    # Apply filters if values are provided
    if name_query:
        doctors = doctors.filter(user__first_name__icontains=name_query) | doctors.filter(user__last_name__icontains=name_query)

    if specialization_query:
        doctors = doctors.filter(specialization__icontains=specialization_query)

    return render(request, 'approved_doctors.html', {'doctors': doctors, 'name_query': name_query, 'specialization_query': specialization_query})

@user_passes_test(is_admin, login_url='login')
def deactivate_doctor(request, doctor_id):
    """ 
    View to deactivate a doctor (set is_approved to False) and send an email notification.
    """
    doctor = get_object_or_404(Doctor, id=doctor_id, is_approved=True)  # Fetch doctor instance

    doctor.is_approved = False  # Deactivate doctor
    doctor.status = "Pending" # Set status to pending
    doctor.save()  # Save the change

    # Send deactivation email
    subject = "Your Doctor Account Has Been Deactivated"
    message = f"""
    Dear {doctor.user.first_name},

    Your account has been deactivated by the admin. If you think this was a mistake, please contact support.

    Best regards,
    Admin Team
    """
    send_status_email(doctor.user.email, subject, message)  # Ensure this function is correctly implemented

    messages.success(request, f"Doctor {doctor.user.username} has been deactivated successfully.")
    
    return redirect('approved_doctors')  # Redirect back to approved doctors list


@user_passes_test(is_admin, login_url='login')
def view_patients(request):
    """ View to list and filter registered patients """
    patients = Patient.objects.select_related('user').all()

    # Get filter values from request
    search_query = request.GET.get('search', '').strip()

    if search_query:
        patients = patients.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__dob__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(admission_number__icontains=search_query)
        )

    return render(request, 'view_patients.html', {
        'patients': patients,
        'search_query': search_query,
    })
    
    
@user_passes_test(is_admin)
def view_appointments(request):
    """ View all appointments with filters """
    appointments = Appointment.objects.select_related('patient', 'doctor')

    # Get filter values from request
    search_query = request.GET.get('search', '').strip()
    filter_date = request.GET.get('date', '')
    filter_status = request.GET.get('status', '')

    if search_query:
        appointments = appointments.filter(
            Q(patient__user__first_name__icontains=search_query) |
            Q(patient__user__last_name__icontains=search_query) |
            Q(doctor__user__first_name__icontains=search_query) |
            Q(doctor__user__last_name__icontains=search_query)
        )

    if filter_date:
        appointments = appointments.filter(date=filter_date)

    if filter_status:
        appointments = appointments.filter(status=filter_status)

    return render(request, 'view_appointments.html', {
        'appointments': appointments,
        'search_query': search_query,
        'filter_date': filter_date,
        'filter_status': filter_status,
    })

@user_passes_test(is_doctor_admin, login_url='login')
#def update_appointment_status(request, appointment_id, new_status):
    #""" Update appointment status (Confirm or Cancel) """
    #appointment = get_object_or_404(Appointment, id=appointment_id)

    #if new_status in ['Confirmed', 'Canceled']:
    #    appointment.status = new_status
    #    appointment.save()
    #    messages.success(request, f"Appointment status updated to {new_status}.")
    #else:
    #    messages.error(request, "Invalid status update.")

    #return redirect('dashboard')
def update_appointment_status(request, appointment_id, new_status):
    """ Update appointment status and redirect user to the appropriate page """

    appointment = get_object_or_404(Appointment, id=appointment_id)

    if new_status in ["Confirmed", "Canceled"]:
        appointment.status = new_status
        appointment.save()
        messages.success(request, f"Appointment status updated to {new_status}.")
    else:
        messages.error(request, "Invalid status update.")

    # Debugging user type
    print(f"User: {request.user}, Type: {request.user.user_type}")  # Check user type

    # Redirect based on user type
    if hasattr(request.user, "user_type"):  # Ensure attribute exists
        if request.user.user_type == "doctor":
            return redirect("doctor_appointments")
        elif request.user.user_type == "admin":
            return redirect("view_appointments")

    return redirect("dashboard")  # Fallback in case of any issues

@login_required
def doctor_availability(request):
    doctor = request.user.doctor # Assuming `DoctorAvailability` has a ForeignKey to User

    if request.method == "POST":
        form = DoctorAvailabilityForm(request.POST, doctor=doctor)
        if form.is_valid():
            availability = form.save(commit=False)
            availability.doctor = doctor  # Ensure the doctor is assigned before saving
            try:
                availability.save()
                return redirect('doctor_availability')  # Change this to the correct URL name
            except ValidationError as e:
                form.add_error(None, e)  # Show error message on form

    else:
        form = DoctorAvailabilityForm(doctor=doctor)

    availabilities = DoctorAvailability.objects.filter(doctor=doctor)

    return render(request, 'doctor_availability.html', {
        'form': form,
        'availabilities': availabilities
    })
@login_required
def delete_availability(request, availability_id):
    availability = get_object_or_404(DoctorAvailability, id=availability_id)

    # Ensure the logged-in user is the owner of the availability
    if request.user.doctor != availability.doctor:
        messages.error(request, "You do not have permission to delete this availability.")
        return redirect('doctor_availability')

    availability.delete()
    messages.success(request, "Availability deleted successfully.")
    return redirect('doctor_availability')


def update_appointment_status(request, appointment_id, new_status):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Allow patients to cancel their own appointments
    if new_status == "Canceled" and appointment.patient.user != request.user and not request.user.is_staff:
        messages.error(request, "You are not authorized to cancel this appointment.")
        return redirect("view_appointments")

    appointment.status = new_status
    appointment.save()
    print("success")
    messages.success(request, f"Appointment has been {new_status.lower()}.")
    #return redirect("view_appointments")
    # Redirect based on user type
    if hasattr(request.user, "user_type"):  # Ensure attribute exists
        if request.user.user_type == "doctor":
            return redirect("doctor_appointment")
        elif request.user.user_type == "admin":
            return redirect("view_appointments")

    return redirect("dashboard")  # Fallback in case of any issues

@login_required
def book_appointment(patient, doctor, date):
    """ Book a 30-minute appointment for the patient on a specific date """

    # Get the day of the week
    day_of_week = date.strftime('%A')  # E.g., 'Monday', 'Tuesday'

    # Get doctor's availability for that day
    availability = DoctorAvailability.objects.filter(doctor=doctor, day=day_of_week).first()

    if not availability:
        raise ValidationError("Doctor is off on this day. Please choose another day.")

    # Find all existing appointments for that day
    existing_appointments = Appointment.objects.filter(doctor=doctor, date=date).order_by('start_time')

    # Start from the doctor's available time
    current_start_time = availability.start_time

    # Check for the first available slot
    while current_start_time < availability.end_time:
        # Calculate end time (30 minutes after start time)
        current_end_time = (datetime.combine(date, current_start_time) + timedelta(minutes=30)).time()

        # Check if this slot is occupied
        overlapping_appointments = existing_appointments.filter(
            start_time__lt=current_end_time,
            end_time__gt=current_start_time
        )

        if not overlapping_appointments.exists():
            # Found an available slot, create the appointment
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                date=date,
                start_time=current_start_time,
                end_time=current_end_time,
                status='Pending'
            )
            return appointment.appointment_id

        # Move to the next 30-minute slot
        current_start_time = current_end_time

    # No available slots
    raise ValidationError("No available slots for this day. Please choose another date.")


# def doctor_appointments_view(request):
#     """
#     Fetches appointments for the logged-in doctor with optional filtering by date, appointment_id, or admission_number.
#     """
#     if not request.user.is_authenticated:
#         return HttpResponse("User is not logged in")

#     if not hasattr(request.user, 'doctor'):
#         return HttpResponse("User is not a doctor")

#     doctor = request.user.doctor
#     date = request.GET.get('date')
#     appointment_id = request.GET.get('appointment_id')
#     admission_number = request.GET.get('admission_number')
    
#     print("reached")

#     # Base query for the doctor's appointments
#     appointments = Appointment.objects.filter(doctor=doctor)
#     print(doctor)

#     # Apply filters if provided
#     if date:
#         appointments = appointments.filter(date=date)
#     if appointment_id:
#         appointments = appointments.filter(appointment_id=appointment_id)
#     if admission_number:
#         appointments = appointments.filter(patient__admission_number=admission_number)

#     # Order results by date and start time
#     appointments = appointments.order_by('date', 'start_time')
#     print(appointments)

#     return render(request, 'doctor_appointments.html', {'appointments': appointments})

from django.utils.timezone import now as timezone_now
from django.utils.timezone import localtime, make_aware
from datetime import datetime
import pytz

def doctor_appointments_view(request):
    """
    Fetches appointments for the logged-in doctor with optional filtering by date, appointment_id, or admission_number.
    """
    if not request.user.is_authenticated:
        return HttpResponse("User is not logged in")
    if not hasattr(request.user, 'doctor'):
        return HttpResponse("User is not a doctor")

    doctor = request.user.doctor
    date = request.GET.get('date')
    appointment_id = request.GET.get('appointment_id')
    admission_number = request.GET.get('admission_number')

    # Base query for the doctor's appointments
    appointments = Appointment.objects.filter(doctor=doctor)

    # Apply filters if provided
    if date:
        appointments = appointments.filter(date=date)
    if appointment_id:
        appointments = appointments.filter(appointment_id=appointment_id)
    if admission_number:
        appointments = appointments.filter(patient__admission_number=admission_number)

    # Order results by date and start time
    appointments = appointments.order_by('date', 'start_time')

    # Get current time in Indian timezone
    indian_tz = pytz.timezone('Asia/Kolkata')
    now = localtime(timezone_now(), indian_tz)  # Ensure `now` is timezone-aware in IST

    for appointment in appointments:
        if appointment.start_time:
            # Make the appointment date-time timezone-aware
            appointment_datetime = datetime.combine(appointment.date, appointment.start_time)
            appointment.full_datetime = make_aware(appointment_datetime, indian_tz)
            
            # Check if appointment time has passed
            appointment.can_update = now >= appointment.full_datetime
        else:
            # Handle cases where start_time is None
            appointment.full_datetime = None
            appointment.can_update = False  # Cannot update if start_time is missing

    return render(request, 'doctor_appointments.html', {
        'appointments': appointments,
    })



@user_passes_test(is_doctor)
def update_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
    print(appointment.id)

    # Ensure only doctors can update status/comments
    if request.user != appointment.doctor.user:
        messages.error(request, "You are not authorized to update this appointment.")
        return redirect('doctor_appointments')

    if request.method == "POST":
        new_status = request.POST.get("status")
        new_comment = request.POST.get("comments")

        if new_status in dict(Appointment.STATUS_CHOICES):
            appointment.status = new_status

        if new_comment:
            appointment.advice = new_comment

        appointment.save()
        patient_email = appointment.patient.user.email
        subject = "New Medical Advice for Your Appointment"
        message = (
                f"Dear {appointment.patient.user.first_name},\n\n"
                f"Dr. {appointment.doctor.user.last_name} has added new advice/comments "
                f"for your appointment on {appointment.date}.\n\n"
                "Please log in to view the details.\n\n"
                "Best regards,\nHospital Management Team"
            )
        send_mail(subject, message, 'noreply@hospital.com', [patient_email], fail_silently=False)
        messages.success(request, "Appointment updated successfully!")
        return redirect('doctor_appointment')

    return render(request, "update_appointment.html", {"appointment": appointment})


import datetime
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect

import datetime
from django.shortcuts import render, redirect
from .models import Appointment, DoctorAvailability

@user_passes_test(is_patient,login_url='login')
def book_appointment_flow(request):
    print(request.user.user_type)
    if request.method == "POST":
        step = request.POST.get("step")

        if step == "1":
            form = AppointmentStep1Form(request.POST)
            if form.is_valid():
                selected_date = form.cleaned_data["date"]
                specialization = form.cleaned_data["specialization"]
                weekday = selected_date.strftime("%A")

                availabilities = DoctorAvailability.objects.filter(
                    day=weekday,
                    doctor__specialization__icontains=specialization
                )

                if not availabilities.exists():
                    form.add_error("date", f"No doctors available on {weekday} for specialization '{specialization}'.")
                    return render(request, "book_appointment_flow.html", {"form": form, "step": 1})

                return render(request, "book_appointment_flow.html", {
                    "step": 2,
                    "availabilities": availabilities,
                    "date": selected_date.strftime("%Y-%m-%d")
                })

            return render(request, "book_appointment_flow.html", {"form": form, "step": 1})

        elif step == "2":
            doctor_id = request.POST.get("doctor_id")
            availability_id = request.POST.get("availability_id")
            selected_date = request.POST.get("date")

            if not (doctor_id and availability_id and selected_date):
                return redirect("book_appointment_flow")

            doctor = get_object_or_404(Doctor, id=doctor_id)
            availability = get_object_or_404(DoctorAvailability, id=availability_id, doctor=doctor)

            #selected_weekday = datetime.datetime.strptime(selected_date, "%Y-%m-%d").strftime("%A")
            selected_weekday = datetime.strptime(selected_date, "%Y-%m-%d").strftime("%A")
            if availability.day != selected_weekday:
                error_message = f"Invalid date selection. Dr. {doctor.user.last_name} is available on {availability.day}."
                return redirect(f"/appointment-status/?error={error_message}")

            return render(request, "book_appointment_flow.html", {
                "step": 3,
                "doctor": doctor,
                "availability": availability,
                "date": selected_date,
                "form": AppointmentStep3Form()
            })

        elif step == "3":
            form = AppointmentStep3Form(request.POST)
            if form.is_valid():
                doctor_id = request.POST.get("doctor_id")
                availability_id = request.POST.get("availability_id")
                selected_date = request.POST.get("date")

                doctor = get_object_or_404(Doctor, id=doctor_id)
                availability = get_object_or_404(DoctorAvailability, id=availability_id, doctor=doctor)

                existing_appointments = Appointment.objects.filter(
                    doctor=doctor,
                    date=selected_date
                ).order_by("start_time")

                current_time = availability.start_time
                while current_time < availability.end_time:
                    #next_time = (datetime.combine(datetime.date.today(), current_time) + datetime.timedelta(minutes=30)).time()
                    next_time = (datetime.combine(date.today(), current_time) + timedelta(minutes=30)).time()
                    if not existing_appointments.filter(start_time=current_time).exists():
                        appointment = Appointment.objects.create(
                            patient=request.user.patient,
                            doctor=doctor,
                            date=selected_date,
                            start_time=current_time,
                            end_time=next_time,
                            symptoms=form.cleaned_data["symptoms"],
                            comments=form.cleaned_data["comments"],
                            status="Pending"
                        )
                        return redirect(f"/appointment-status/?success=1&appointment_id={appointment.appointment_id}")

                    current_time = next_time
                    if current_time >= availability.end_time:
                        break

                return redirect("/appointment-status/?error=No available slots for the selected date.")

    return render(request, "book_appointment_flow.html", {"form": AppointmentStep1Form(), "step": 1})

def appointment_status(request):
    success = request.GET.get("success")
    appointment_id = request.GET.get("appointment_id", "")
    error_message = request.GET.get("error", "")

    # Fetch the appointment details from the database
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id) if appointment_id else None

    # Prepare the message if the appointment is successful
    early_arrival_message = ""
    if success and appointment:
        early_arrival_message = f"Please arrive at least 30 minutes before your scheduled time at {appointment.start_time}."

    return render(request, "appointment_status.html", {
        "success": success,
        "appointment": appointment,
        "error_message": error_message,
        "early_arrival_message": early_arrival_message,
    })


@login_required
def view_doctor_comments(request, appointment_id):
    """
    Allows a patient (or the doctor) to view the doctor's advice/comments for an appointment.
    Only the patient or the doctor involved in the appointment may view the comments.
    """
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
    
    # Check that the user is either the patient or the doctor associated with this appointment.
    if request.user != appointment.patient.user and request.user != appointment.doctor.user:
        return HttpResponse("Unauthorized", status=401)
    
    return render(request, "view_comments.html", {"appointment": appointment})

from django.shortcuts import render
from django.db.models import Q
from .models import Doctor, DoctorAvailability
from datetime import datetime

def doctors_view_patient(request):
    specialization = request.GET.get('specialization', '')
    name = request.GET.get('name', '')
    day = request.GET.get('day', datetime.today().strftime('%A'))
    
    doctors = Doctor.objects.filter(status='Approved', is_approved=True)
    
    if specialization:
        doctors = doctors.filter(specialization__icontains=specialization)
    if name:
        doctors = doctors.filter(Q(user__first_name__icontains=name) | Q(user__last_name__icontains=name))
    if day:
        doctors = doctors.filter(availabilities__day=day).distinct()

    paginator = Paginator(doctors, 3)
    page = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'page_obj': page_obj,
        'specialization': specialization,
        'name': name,
        'day': day,
    }
    return render(request, 'doctors_list.html', context)


def patient_appointments_view(request):
    # Get the logged-in patient (assuming authentication is set up)
    patient = get_object_or_404(Patient, user=request.user)

    # Fetch all appointments for the patient
    appointments = Appointment.objects.filter(patient=patient).order_by('-date', 'start_time')

    # Filter logic based on query parameters
    query = request.GET.get('query', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status')

    if query:
        appointments = appointments.filter(
            Q(doctor__user__first_name__icontains=query) |
            Q(doctor__user__last_name__icontains=query)
        )
    if start_date:
        appointments = appointments.filter(date__gte=start_date)
    if end_date:
        appointments = appointments.filter(date__lte=end_date)
    if status:
        appointments = appointments.filter(status=status)

    context = {
        'appointments': appointments,
        'query': query,
        'start_date': start_date,
        'end_date': end_date,
        'status': status,
    }

    return render(request, 'patient_appointments.html', context)


from django.http import JsonResponse
from .predict import predict_disease
import pandas as pd


def predict_view(request):
    symptoms = request.GET.get("symptoms", "")
    if not symptoms:
        return JsonResponse({"error": "No symptoms provided"}, status=400)

    result = predict_disease(symptoms)
    return JsonResponse(result)


# Load trained models
rf_model = joblib.load("models/rf_model.pkl")
nb_model = joblib.load("models/nb_model.pkl")
svm_model = joblib.load("models/svm_model.pkl")

encoder = joblib.load("models/label_encoder.pkl")

# Load dataset to get symptoms
data = pd.read_csv("dataset.csv")
symptoms_list = list(data.columns[:-1])  # Extract all symptom names

@login_required
def predict_page(request):
    """Renders the HTML page with symptom selection."""
    return render(request, "predict.html", {"symptoms": symptoms_list})

@login_required
def predict_disease(request):
    """Predicts disease based on user symptoms."""
    symptoms = request.GET.get("symptoms", "").split(",")
    input_data = [1 if symptom in symptoms else 0 for symptom in symptoms_list]

    rf_prediction = rf_model.predict([input_data])[0]
    nb_prediction = nb_model.predict([input_data])[0]
    svm_prediction = svm_model.predict([input_data])[0]

    # Convert numerical labels back to disease names
    rf_prediction_name = encoder.inverse_transform([rf_prediction])[0]
    nb_prediction_name = encoder.inverse_transform([nb_prediction])[0]
    svm_prediction_name = encoder.inverse_transform([svm_prediction])[0]

    # Majority vote for final prediction
    predictions = [rf_prediction_name, nb_prediction_name, svm_prediction_name]
    final_prediction = max(set(predictions), key=predictions.count)

    return JsonResponse({
        "Final Prediction": final_prediction,
        "Random Forest": rf_prediction_name,
        "Naive Bayes": nb_prediction_name,
        "SVM": svm_prediction_name,
    })

# def doctor_appointments_view(request):
#     # Get the logged-in patient (assuming authentication is set up)
#     doctor = get_object_or_404(Doctor, user=request.user)

#     # Fetch all appointments for the patient
#     appointments = Appointment.objects.filter(doctor=doctor).order_by('-date', 'start_time')

#     # Filter logic based on query parameters
#     query = request.GET.get('query', '')
#     start_date = request.GET.get('start_date')
#     end_date = request.GET.get('end_date')
#     status = request.GET.get('status')

#     if query:
#         appointments = appointments.filter(
#             Q(doctor__user__first_name__icontains=query) |
#             Q(doctor__user__last_name__icontains=query)
#         )
#     if start_date:
#         appointments = appointments.filter(date__gte=start_date)
#     if end_date:
#         appointments = appointments.filter(date__lte=end_date)
#     if status:
#         appointments = appointments.filter(status=status)

#     context = {
#         'appointments': appointments,
#         'query': query,
#         'start_date': start_date,
#         'end_date': end_date,
#         'status': status,
#     }

#     return render(request, 'doctor_appointments.html', context)


@login_required
def consulted_patients_list(request):
    if not hasattr(request.user, 'doctor'):
        return redirect('dashboard')  # Redirect unauthorized users

    doctor = request.user.doctor
    patients = Appointment.objects.filter(doctor=doctor).order_by('-date')

    # Get distinct patients by grouping them
    unique_patients = patients.values(
        'patient__user__first_name',
        'patient__user__last_name',
        'patient__admission_number',
        'patient_id'
    ).annotate(appointment_count=Count('id'))

    # Filtering
    name_query = request.GET.get('name', '').strip()
    admission_number_query = request.GET.get('admission_number', '').strip()

    if name_query:
        unique_patients = unique_patients.filter(
            patient__user__first_name__icontains=name_query
        ) | unique_patients.filter(
            patient__user__last_name__icontains=name_query
        )

    if admission_number_query:
        unique_patients = unique_patients.filter(
            patient__admission_number__icontains=admission_number_query
        )

    context = {
        'patients': unique_patients,
        'name_query': name_query,
        'admission_number_query': admission_number_query,
    }
    return render(request, 'consulted_patients.html', context)


@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    appointments = Appointment.objects.filter(patient=patient).order_by('-date')

    context = {
        'patient': patient,
        'appointments': appointments,
    }
    return render(request, 'patient_detail.html', context)


@login_required
def add_vitals(request, appointment_id):
    """Allows the assigned nurse to add vitals for an appointment."""
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Ensure only the assigned nurse can add vitals
    if request.user != appointment.nurse.user:
        messages.error(request, "You are not authorized to add vitals for this appointment.")
        return redirect("dashboard")  # Redirect to nurse dashboard

    # Check if vitals already exist
    vitals_record, created = VitalsRecord.objects.get_or_create(appointment=appointment)

    if request.method == "POST":
        form = VitalsRecordForm(request.POST, instance=vitals_record)
        if form.is_valid():
            vitals_record = form.save(commit=False)
            vitals_record.nurse = appointment.nurse  # Auto-assign nurse
            vitals_record.save()
            messages.success(request, "Vitals recorded successfully!")
            return redirect("appointment_detail", appointment_id=appointment.id)
    else:
        form = VitalsRecordForm(instance=vitals_record)

    return render(request, "add_vitals.html", {"form": form, "appointment": appointment})


@login_required
def view_appointments_nurse(request):
    """Displays all appointments assigned to the logged-in nurse."""
    nurse = request.user.nurse  # Assuming `Nurse` model is related to `User`
    appointments = Appointment.objects.filter(nurse=nurse).order_by('-date')

    return render(request, "view_appointments_nurse.html", {"appointments": appointments})


@login_required
def submit_feedback(request):
    if request.method == "POST":
        message = request.POST.get("message")
        if message:
            Feedback.objects.create(user=request.user, message=message)
            messages.success(request, "Feedback submitted successfully!")
        else:
            messages.error(request, "Message cannot be empty.")
    return render(request, "submit_feedback.html")

@user_passes_test(is_admin)
def feedback_list(request):
    feedbacks = Feedback.objects.all()
    return render(request, "feedback_list.html", {"feedbacks": feedbacks})

@user_passes_test(is_admin)
def admin_reply_feedback(request, feedback_id):
    if not request.user.is_superuser:
        messages.error(request, "Unauthorized access!")
        return redirect("feedback_list")

    feedback = get_object_or_404(Feedback, id=feedback_id)

    if request.method == "POST":
        reply = request.POST.get("reply")
        feedback.reply = reply
        feedback.save()
        messages.success(request, "Reply added successfully!")
        return redirect("feedback_list")

    return render(request, "admin_reply_feedback.html", {"feedback": feedback})


@login_required
def user_feedback_list(request):
    feedbacks = Feedback.objects.filter(user=request.user)
    return render(request, "user_feedback_list.html", {"feedbacks": feedbacks})


@login_required
def change_shift_view(request):
    nurse = getattr(request.user, 'nurse', None)  # Get nurse object if exists

    if not nurse:
        messages.error(request, "You are not authorized to change shift.")
        return redirect("dashboard")  

    if request.method == "POST":
        new_shift = request.POST.get("new_shift")  
        if new_shift:
            nurse.shift = new_shift
            nurse.save()
            messages.success(request, f"Shift changed to {new_shift} successfully!")
        else:
            messages.error(request, "Invalid shift selection.")

    return render(request, "change_shift.html", {"nurse": nurse})
