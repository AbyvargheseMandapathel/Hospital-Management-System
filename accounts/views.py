from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib import messages
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from .utils import send_status_email
from django.db.models import Q
from datetime import time
from .forms import *
from django.utils.timezone import datetime, timedelta
from django.http import HttpResponse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from .forms import *


# Create your views here.

def home(request):
    return render(request, 'home.html')

User = get_user_model()  # Fetch the custom user model if defined
def signup(request):
    if request.method == "POST":
        # Retrieve common fields
        username   = request.POST.get('username')
        password   = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name  = request.POST.get('last_name')
        email      = request.POST.get('email')
        place      = request.POST.get('place')
        dob        = request.POST.get('dob')
        user_type  = request.POST.get('user_type')
        
        # Print common fields to the terminal for debugging
        print("Username:", username)
        print("Password:", password)
        print("First Name:", first_name)
        print("Last Name:", last_name)
        print("Email:", email)
        print("Place:", place)
        print("Date of Birth:", dob)
        print("User Type:", user_type)

        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            print("if condition check")
            messages.error(request, "Username already exists.")
            return redirect('signup')
        if User.objects.filter(email=email).exists():
            print("all ready exit")

            messages.error(request, "Email already exists.")
            return redirect('signup')

        try:
            # Create the user instance
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
            print(user,"wow")
            # Handle user-type specific fields
            if user_type == 'nurse':
                print(user_type,"nurse" )
                # Use 'nurse_phone' from the form; pass it to the Nurse model as phone_number.
                nurse_phone = request.POST.get('nurse_phone')
                print(nurse_phone,'this is nurse ph')
                shift = request.POST.get('shift')
                Nurse.objects.create(user=user, phone_number=nurse_phone, shift=shift)

            elif user_type == 'doctor':
                # Use 'doctor_phone' from the form; pass it to the Doctor model as phone_number.
                doctor_phone = request.POST.get('doctor_phone')
                print(doctor_phone,"hi ph")

                specialization = request.POST.get('specialization')
                print(specialization,"hi spec")
                
                experience = request.POST.get('experience')
                print(experience,"hi exp")

                certificate_file = request.FILES.get('certificate_file')
                print(certificate_file,"hi cert")

                # If your model field is named 'certificate_files', pass it as such.
                Doctor.objects.create(
                    user=user,
                    specialization=specialization,
                    experience=experience,
                    phone_number=doctor_phone,
                    certificate_files=certificate_file
                )

            elif user_type == 'patient':
                # Use 'patient_phone' from the form; pass it to the Patient model as phone_number.
                patient_phone = request.POST.get('patient_phone')
                print(patient_phone,'this is pat ph')

                Patient.objects.create(user=user, phone_number=patient_phone)

            messages.success(request, "Signup successful! Please log in.")
            return redirect('login')

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('signup')

    # If the request method is not POST, render the signup form.
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

def is_doctor(user):
    return user.is_authenticated and hasattr(user, 'doctor') and user.doctor.is_approved

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
    
    
@user_passes_test(is_admin, login_url='login')
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

@user_passes_test(is_admin, login_url='login')
def update_appointment_status(request, appointment_id, new_status):
    """ Update appointment status (Confirm or Cancel) """
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if new_status in ['Confirmed', 'Canceled']:
        appointment.status = new_status
        appointment.save()
        messages.success(request, f"Appointment status updated to {new_status}.")
    else:
        messages.error(request, "Invalid status update.")

    return redirect('view_appointments')

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
    
    messages.success(request, f"Appointment has been {new_status.lower()}.")
    return redirect("view_appointments")


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
    
    print("reached")

    # Base query for the doctor's appointments
    appointments = Appointment.objects.filter(doctor=doctor)
    print(doctor)

    # Apply filters if provided
    if date:
        appointments = appointments.filter(date=date)
    if appointment_id:
        appointments = appointments.filter(appointment_id=appointment_id)
    if admission_number:
        appointments = appointments.filter(patient__admission_number=admission_number)

    # Order results by date and start time
    appointments = appointments.order_by('date', 'start_time')
    print(appointments)

    return render(request, 'doctor_appointments.html', {'appointments': appointments})


@user_passes_test(is_doctor)
def update_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)

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

@login_required
def book_appointment_flow(request):
    if request.method == "POST":
        step = request.POST.get("step")
        if step == "1":
            # Step 1: Patient selects a date and enters specialization.
            form = AppointmentStep1Form(request.POST)
            if form.is_valid():
                selected_date = form.cleaned_data["date"]  # Date object
                specialization = form.cleaned_data["specialization"]
                # Convert the selected date into a weekday name (e.g., "Monday")
                weekday = selected_date.strftime("%A")
                # Filter availabilities where the doctor's specialization contains the entered text
                availabilities = DoctorAvailability.objects.filter(
                    day=weekday,
                    doctor__specialization__icontains=specialization
                )
                if not availabilities.exists():
                    form.add_error("date", f"No doctors available on {weekday} for specialization '{specialization}'.")
                    return render(request, "book_appointment_flow.html", {"form": form, "step": 1})
                # Pass the selected date as a string (YYYY-MM-DD) to the next step
                context = {
                    "step": 2,
                    "availabilities": availabilities,
                    "date": selected_date.strftime("%Y-%m-%d")
                }
                return render(request, "book_appointment_flow.html", context)
            else:
                return render(request, "book_appointment_flow.html", {"form": form, "step": 1})
        
        elif step == "2":
            # Step 2: Patient selects a doctor and time slot.
            doctor_id = request.POST.get("doctor_id")
            availability_id = request.POST.get("availability_id")
            selected_date = request.POST.get("date")  # in YYYY-MM-DD string format
            if not (doctor_id and availability_id and selected_date):
                return redirect("book_appointment_flow")
            doctor = get_object_or_404(Doctor, id=doctor_id)
            availability = get_object_or_404(DoctorAvailability, id=availability_id, doctor=doctor)
            # Validate that the chosen date’s weekday matches the doctor's availability.
            selected_weekday = datetime.datetime.strptime(selected_date, "%Y-%m-%d").strftime("%A")
            if availability.day != selected_weekday:
                error_message = f"Invalid date selection. Dr. {doctor.user.last_name} is available on {availability.day}."
                availabilities = DoctorAvailability.objects.filter(day=selected_weekday, doctor=doctor)
                return render(request, "book_appointment_flow.html", {
                    "step": 2,
                    "availabilities": availabilities,
                    "date": selected_date,
                    "error": error_message
                })
            # Proceed to Step 3.
            form = AppointmentStep3Form()
            context = {
                "step": 3,
                "doctor": doctor,
                "availability": availability,
                "date": selected_date,
                "form": form
            }
            return render(request, "book_appointment_flow.html", context)
        
        elif step == "3":
            # Step 3: Patient enters symptoms and additional notes.
            form = AppointmentStep3Form(request.POST)
            if form.is_valid():
                doctor_id = request.POST.get("doctor_id")
                availability_id = request.POST.get("availability_id")
                selected_date = request.POST.get("date")
                doctor = get_object_or_404(Doctor, id=doctor_id)
                availability = get_object_or_404(DoctorAvailability, id=availability_id, doctor=doctor)
                # Create the appointment
                appointment  = Appointment.objects.create(
                    patient=request.user.patient,
                    doctor=doctor,
                    date=selected_date,
                    start_time=availability.start_time,
                    end_time=availability.end_time,
                    symptoms=form.cleaned_data["symptoms"],
                    comments=form.cleaned_data["comments"],
                    status="Pending"
                )
                return HttpResponse(appointment.appointment_id)
            else:
                doctor = get_object_or_404(Doctor, id=request.POST.get("doctor_id"))
                availability = get_object_or_404(DoctorAvailability, id=request.POST.get("availability_id"), doctor=doctor)
                context = {
                    "step": 3,
                    "doctor": doctor,
                    "availability": availability,
                    "date": request.POST.get("date"),
                    "form": form
                }
                return render(request, "book_appointment_flow.html", context)
    else:
        form = AppointmentStep1Form()
    return render(request, "book_appointment_flow.html", {"form": form, "step": 1})


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

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Appointment

