import random
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
import uuid
from django.utils import timezone
import datetime



# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username field must be set")
        extra_fields.setdefault("is_active", True)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("user_type", "admin")  # Automatically set to admin

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, password, **extra_fields)

# Profile model to serve as the base user model
class Profile(AbstractUser):
    place = models.CharField(max_length=255, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
 
    USER_TYPE_CHOICES = [
        ('admin', 'Admin'),
        ('patient', 'Patient'),
        ('nurse', 'Nurse'),
        ('doctor', 'Doctor'),
    ]
    user_type = models.CharField(max_length=7, choices=USER_TYPE_CHOICES, default='patient')
    is_approved = models.BooleanField(default=False)

    objects = CustomUserManager()

    # Avoid conflicts by setting custom related names for groups and user_permissions
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
# Nurse model
class Nurse(models.Model):
    user = models.OneToOneField('accounts.Profile', on_delete=models.CASCADE, related_name='nurse')
    phone_number = models.CharField(max_length=15)
    shift = models.CharField(max_length=50, help_text="Shift timing (e.g., Morning, Evening, Night)")
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Nurse: {self.user.first_name} {self.user.last_name} ({self.shift})"
    
def generate_doctor_number():
    count = Doctor.objects.count() + 1
    return f"DOC{count:04d}2025"

# Doctor model
class Doctor(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.OneToOneField('accounts.Profile', on_delete=models.CASCADE, related_name='doctor')
    phone_number = models.CharField(max_length=15)
    specialization = models.TextField()
    experience = models.PositiveIntegerField(help_text="Number of years of experience")
    certificate_files = models.FileField(upload_to='certificates/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    is_approved = models.BooleanField(default=False)
    doctor_number = models.CharField(max_length=20, unique=True, editable=False)

    def __str__(self):
        return f"Doctor: {self.user.first_name} {self.user.last_name} ({self.status})"

    
    def save(self, *args, **kwargs):
        if not self.doctor_number:
            self.doctor_number = generate_doctor_number()
        super().save(*args, **kwargs)

# Function to generate admission number for the Patient model
def generate_admission_number():
    count = Patient.objects.count() + 1
    return f"PAT{count:04d}2025"

# Patient model
class Patient(models.Model):
    user = models.OneToOneField('accounts.Profile', on_delete=models.CASCADE, related_name='patient')
    phone_number = models.CharField(max_length=15, unique=True)
    admission_number = models.CharField(max_length=20, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.admission_number:
            self.admission_number = generate_admission_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Patient: {self.user.first_name} {self.user.last_name} ({self.phone_number}, {self.admission_number})"
    
    
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Completed', 'Completed'),
        ('Canceled', 'Canceled'),
    ]

    appointment_id = models.CharField(max_length=50, unique=True, editable=False)
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE)
    nurse = models.ForeignKey('Nurse', on_delete=models.SET_NULL, null=True, blank=True)  # New field
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True, default=None)
    end_time = models.TimeField(null=True, blank=True, default=None)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Pending')
    advice = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    comments = models.CharField(max_length=1500)
    symptoms = models.CharField(max_length=1500)

    class Meta:
        ordering = ['-date', 'start_time']
        unique_together = ('doctor', 'date', 'start_time')

    def __str__(self):
        start_time_str = self.start_time.strftime("%H:%M:%S") if self.start_time else "TBD"
        end_time_str = self.end_time.strftime("%H:%M:%S") if self.end_time else "TBD"
        return (f"Appointment {self.appointment_id} - Dr. {self.doctor.user.last_name} "
                f"with {self.patient.user.first_name} on {self.date} from {start_time_str} to {end_time_str}")

    def save(self, *args, **kwargs):
        if not self.appointment_id:
            self.appointment_id = self.generate_appointment_id()
        # Ensure end_time is after start_time
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("End time must be after start_time.")

        # Auto-assign a random nurse when status changes to Confirmed
        if self.status == "Confirmed" and not self.nurse:
            self.assign_random_nurse()

        super().save(*args, **kwargs)

    def generate_appointment_id(self):
        if isinstance(self.date, str):
            try:
                self.date = datetime.datetime.strptime(self.date, "%Y-%m-%d").date()
            except ValueError:
                raise ValidationError("Date format is invalid; expected YYYY-MM-DD.")

        counter = Appointment.objects.filter(doctor=self.doctor, date=self.date).count() + 1
        date_str = self.date.strftime("%Y%m%d")
        return f"{self.doctor.doctor_number}-{date_str}-{counter:03d}"

    def is_upcoming(self):
        now = timezone.now().date()
        return self.date >= now

    def is_past(self):
        now = timezone.now().date()
        return self.date < now

    def assign_random_nurse(self):
        """Assign a random available nurse to this appointment."""
        nurses = Nurse.objects.filter(is_approved=True)
        if nurses.exists():
            self.nurse = random.choice(nurses)
    
    
class DoctorAvailability(models.Model):
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE, related_name='availabilities')
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ('doctor', 'day', 'start_time', 'end_time')

    def clean(self):
        """Ensure start time is before end time and prevent overlapping slots."""
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")

        # overlapping_availability = DoctorAvailability.objects.filter(
        #     doctor=self.doctor,
        #     day=self.day
        # ).exclude(id=self.id).filter(
        #     start_time__lt=self.end_time,
        #     end_time__gt=self.start_time
        # )

        # if overlapping_availability.exists():
        #     raise ValidationError("This time slot overlaps with an existing availability.")

    def save(self, *args, **kwargs):
        self.full_clean()  # Run validations before saving
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.doctor.user.username} - {self.day}: {self.start_time} to {self.end_time}"
    
    
class VitalsRecord(models.Model):
    """Model to store patient vitals recorded by the assigned nurse."""
    appointment = models.OneToOneField(
        'Appointment', on_delete=models.CASCADE, related_name="vitals"
    )
    nurse = models.ForeignKey('Nurse', on_delete=models.SET_NULL, null=True, blank=True)
    sugar_level = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cholesterol_level = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    blood_pressure_systolic = models.PositiveIntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.PositiveIntegerField(null=True, blank=True)
    heart_rate = models.PositiveIntegerField(null=True, blank=True)
    oxygen_saturation = models.PositiveIntegerField(null=True, blank=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"Vitals for {self.appointment.patient.user.get_full_name()} on {self.recorded_at.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs):
        """Ensure the nurse is the one assigned to the appointment."""
        if self.appointment.nurse:
            self.nurse = self.appointment.nurse  # Auto-assign nurse from appointment
        else:
            raise ValueError("Vitals can only be recorded if an appointment has an assigned nurse.")
        super().save(*args, **kwargs)
        
        
class Feedback(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    message = models.TextField()
    reply = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.user.username}"
