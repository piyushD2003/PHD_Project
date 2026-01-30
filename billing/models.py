from django.db import models
from django.conf import settings
# from doctor.models import DoctorProfile
# from doctor.models import Clinic  
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from insurance.models import Insurance
from django.contrib.auth.models import User

class AccountantProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='accountant_profile')
    clinic = models.ForeignKey("doctor.Clinic", on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    department = models.CharField(max_length=100)
    profile_pic = models.ImageField(upload_to='accountant_profiles/', blank=True, null=True)

    def __str__(self):
        return f"Accountant: {self.user.username} ({self.department})"

class Billing(models.Model):
    BILLING_TYPE_CHOICES = [
        ('Hospital', 'Hospital Bill'),
        ('LabTest', 'Lab Test Bill'),
        ('Medical', 'Medical Bill'),
        ('Doctor', 'Doctor Bill'),
    ]
    
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    doctor = models.ForeignKey("doctor.DoctorProfile", on_delete=models.SET_NULL, null=True, blank=True)
    clinic = models.ForeignKey("doctor.Clinic", on_delete=models.SET_NULL, null=True, blank=True)

    billing_type = models.CharField(
        max_length=20,
        choices=BILLING_TYPE_CHOICES,
        default='Hospital'  
    )

    insurance_claim = models.ForeignKey(
        Insurance, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='bills'
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    source = GenericForeignKey('content_type', 'object_id')

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)

    payment_method = models.CharField(
        max_length=50,
        choices=[('Cash', 'Cash'), ('Card', 'Card'), ('UPI', 'UPI')],
        default='Cash'
    )
    paid_by = models.CharField(
        max_length=50,
        choices=[('Patient', 'Patient'), ('Insurance', 'Insurance'), ('Other', 'Other'),],
        null=True, 
        blank=True, 
    )
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.billing_type} for {self.patient.username} on {self.date}"
    

