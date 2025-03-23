from django import forms
from django.core.exceptions import ValidationError
from .models import *
from datetime import date

class DoctorAvailabilityForm(forms.ModelForm):
    class Meta:
        model = DoctorAvailability
        fields = ['day', 'start_time', 'end_time']
        widgets = {
            'day': forms.Select(attrs={'class': 'mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm text-black'}),
            'start_time': forms.TimeInput(attrs={'class': 'mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm text-black', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm text-black', 'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        self.doctor = kwargs.pop('doctor', None)  # Get doctor from kwargs
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        day = cleaned_data.get("day")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if not self.doctor:
            raise ValidationError("Doctor is required.")

        if start_time and end_time and start_time >= end_time:
            raise ValidationError("Start time must be before end time.")

        # Check for overlapping availability slots
        overlapping_availabilities = DoctorAvailability.objects.filter(
            doctor=self.doctor,  # Use self.doctor instead of self.instance.doctor
            day=day,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exclude(id=self.instance.id if self.instance else None)

        if overlapping_availabilities.exists():
            # Merge overlapping slots
            first_overlap = overlapping_availabilities.first()
            first_overlap.start_time = min(first_overlap.start_time, start_time)
            first_overlap.end_time = max(first_overlap.end_time, end_time)
            first_overlap.save()
            raise ValidationError("Overlapping availability detected. Merged with an existing slot.")

        return cleaned_data
    
class DoctorSelectionForm(forms.Form):
    specialization = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}))
    date = forms.DateField(widget=forms.DateInput(attrs={'class': 'mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm', 'type': 'date'}))

class AppointmentStep1Form(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md',
             'min': date.today().strftime("%Y-%m-%d"),  # Restrict past dates
        }),
        required=True
    )
    specialization = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
           'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md',
            'placeholder': 'Enter specialization'
        }),
        required=True
    )


class AppointmentStep3Form(forms.Form):
    symptoms = forms.CharField(
        max_length=1500,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md',
            'rows': 3,
            'placeholder': 'Describe your symptoms'
        }),
        required=True
    )
    comments = forms.CharField(
        max_length=1500,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md',
            'rows': 3,
            'placeholder': 'Enter any additional notes'
        }),
        required=False
    )
    
    
class VitalsRecordForm(forms.ModelForm):
    """Form for nurses to input patient vitals."""
    class Meta:
        model = VitalsRecord
        fields = [
            "sugar_level", "cholesterol_level", "blood_pressure_systolic", "blood_pressure_diastolic",
            "heart_rate", "oxygen_saturation", "temperature", "notes"
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3, "class": "form-input"})
        }
        
        

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'email', 'place', 'dob']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md text-black',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md text-black',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md text-black',
            }),
            'place': forms.TextInput(attrs={
                'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md text-black',
            }),
            'dob': forms.DateInput(attrs={
                'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md text-black',
                'type': 'date',
                'max': date.today().strftime("%Y-%m-%d"),  # Restrict future dates
            }),
        }
        
class NurseUpdateForm(forms.ModelForm):
    SHIFT_CHOICES = [
        ('Morning', 'Morning'),
        ('Evening', 'Evening'),
    ]

    phone_number = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md text-black',
            'pattern': '[0-9]{10}',
            'title': 'Please enter a 10-digit phone number'
        })
    )
    
    shift = forms.ChoiceField(
        choices=SHIFT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md text-black',
        })
    )
    
    class Meta:
        model = Nurse
        fields = ['phone_number', 'shift']

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            raise forms.ValidationError("Phone number is required")
        if not phone_number.isdigit():
            raise forms.ValidationError("Phone number must contain only digits")
        if len(phone_number) != 10:
            raise forms.ValidationError("Phone number must be exactly 10 digits")
        return phone_number

class DoctorUpdateForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['phone_number', 'specialization', 'experience']
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md text-black',
            }),
            'specialization': forms.TextInput(attrs={
                'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md text-black',
            }),
            'experience': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md text-black',
            }),
        }
        
class LeaveApplicationForm(forms.ModelForm):
    class Meta:
        model = LeaveApplication
        fields = ['start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={
                'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md text-black',
                'type': 'date',
                'min': date.today().strftime("%Y-%m-%d"),
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md text-black',
                'type': 'date',
                'min': date.today().strftime("%Y-%m-%d"),
            }),
            'reason': forms.Textarea(attrs={
                'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md text-black',
                'rows': 4,
            }),
        }

class PatientUpdateForm(forms.ModelForm):
    phone_number = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full p-2 border border-gray-300 rounded-md text-black',
            'pattern': '[0-9]{10}',
            'title': 'Please enter a 10-digit phone number'
        })
    )
    
    class Meta:
        model = Patient
        fields = ['phone_number']