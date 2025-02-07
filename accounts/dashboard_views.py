from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from .models import *  
from datetime import date

@login_required
def patient_dashboard(request):
    return render(request, 'patient_dashboard.html')

@login_required
def doctor_dashboard(request):
    return render(request, 'doctor_dashboard.html')

@login_required
def nurse_dashboard(request):
    return render(request, 'nurse_dashboard.html')