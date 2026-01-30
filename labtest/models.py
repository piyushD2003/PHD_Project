from django.db import models
from django.contrib.auth.models import User
from doctor.models import Clinic, DoctorProfile
from billing.models import Billing
from patient.models import PatientProfile

class LabStaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='labstaff_profile')
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    qualification = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ])
    age = models.PositiveIntegerField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='labstaff_profiles/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.user.username})"

class LabTest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
    ]

    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE)
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    clinic = models.ForeignKey(Clinic, on_delete=models.SET_NULL, null=True, blank=True)
    billing = models.ForeignKey(Billing, on_delete=models.SET_NULL, null=True, blank=True, related_name='lab_tests')
    labstaff = models.ForeignKey(LabStaffProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='labtests')

    test_type = models.CharField(max_length=100)
    test_date = models.DateField(auto_now_add=True)
    finding = models.TextField(blank=True, null=True)
    diagnosis = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    report_file = models.FileField(upload_to='labtest_reports/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.test_type} - {self.patient.name if self.patient else 'No Patient'}"

    def save(self, *args, **kwargs):
        # Auto-assign the default clinic if not set
        if not self.clinic:
            self.clinic = Clinic.objects.first()
        super().save(*args, **kwargs)

    def approve_test(self, labstaff, finding, diagnosis, report_file, amount):
        self.labstaff = labstaff
        self.finding = finding
        self.diagnosis = diagnosis
        self.report_file = report_file
        self.amount = amount
        self.status = 'Approved'
        self.save()

    def is_pending(self):
        return self.status == 'Pending'

    def is_approved(self):
        return self.status == 'Approved'
