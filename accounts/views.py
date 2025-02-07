from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib import messages
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from .utils import send_status_email
from django.db.models import Q
# Create your views here.


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

                specification = request.POST.get('specification')
                print(specification,"hi spec")
                
                experience = request.POST.get('experience')
                print(experience,"hi exp")

                certificate_file = request.FILES.get('certificate_file')
                print(certificate_file,"hi cert")

                # If your model field is named 'certificate_files', pass it as such.
                Doctor.objects.create(
                    user=user,
                    specification=specification,
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

        doctor.delete()  # Remove doctor profile
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
    """ View to deactivate a doctor (set is_approved to False) and send email """
    try:
        doctor = Profile.objects.get(id=doctor_id, user_type='doctor', is_approved=True)
        doctor.is_approved = False  # Deactivate doctor
        doctor.save()

        # Send deactivation email
        subject = "Your Doctor Account Has Been Deactivated"
        message = f"Dear {doctor.user.first_name},\n\nYour account has been deactivated by the admin. If you think this was a mistake, please contact support.\n\nBest regards,\nAdmin Team"
        send_status_email(doctor.user.email, subject, message)

        messages.success(request, f"Doctor {doctor.user.username} has been deactivated successfully.")
    except Profile.DoesNotExist:
        messages.error(request, "Doctor not found or already deactivated.")
    
    return redirect('approved_doctors')


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
    """ View for doctors to set their availability """
    if request.method == "POST":
        selected_days = request.POST.getlist('days')  # Get selected days
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        if not selected_days or not start_time or not end_time:
            messages.error(request, "Please select at least one day and provide valid time slots.")
            return redirect('doctor_availability')

        # Remove existing availabilities for this doctor
        DoctorAvailability.objects.filter(doctor=request.user).delete()

        # Save new availabilities
        for day in selected_days:
            DoctorAvailability.objects.create(
                doctor=request.user,
                day=day,
                start_time=start_time,
                end_time=end_time
            )

        messages.success(request, "Availability updated successfully!")
        return redirect('doctor_availability')

    # Fetch existing availability for the logged-in doctor
    existing_availabilities = DoctorAvailability.objects.filter(doctor=request.user)
    selected_days = [availability.day for availability in existing_availabilities]
    
    return render(request, "doctor_availability.html", {
        "selected_days": selected_days,
        "existing_availabilities": existing_availabilities,
    })