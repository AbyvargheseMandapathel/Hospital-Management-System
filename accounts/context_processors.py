from django.urls import reverse
from django.shortcuts import redirect

def base_template_processor(request):
    # Default base template
    base_template = None

    # Check if the user is authenticated
    if request.user.is_authenticated:
        user_type = getattr(request.user, 'user_type', None)
        if user_type == 'admin':
            base_template = 'base/admin_base.html'
        elif user_type == 'nurse':
            base_template = 'base/nurse_base.html'
        elif user_type == 'patient':
            base_template = 'base/patient_base.html'
        elif user_type == 'doctor':
            base_template = 'base/doctor_base.html'
    
    # If no valid user_type, redirect to login (optional)
    if not base_template and request.user.is_authenticated:
        return redirect(reverse('login'))

    return {
        'base_template': base_template,
    }