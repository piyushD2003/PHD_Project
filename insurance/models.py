from django.db import models
from django.contrib.auth.models import User

    
    
class InsuranceProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='insurance_profile')
    clinic = models.ForeignKey("doctor.Clinic", on_delete=models.CASCADE)
        
    company_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    department = models.CharField(max_length=100)
    profile_pic = models.ImageField(upload_to='insurance_profiles/', blank=True, null=True)

    def __str__(self):
            return f"{self.user.username} - {self.company_name}"

class Insurance(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    POLICY_TYPE_CHOICES = [
        ('Individual', 'Individual'),
        ('Family', 'Family'),
        ('Corporate', 'Corporate'),
    ]

    patient = models.ForeignKey("patient.PatientProfile", on_delete=models.CASCADE, null=True, blank=True, related_name='insurances')
    doctor = models.ForeignKey("doctor.DoctorProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name='insurances')
    clinic = models.ForeignKey("doctor.Clinic", on_delete=models.SET_NULL, null=True, blank=True, related_name='insurances')
    billing = models.ForeignKey("billing.Billing", on_delete=models.SET_NULL, null=True, blank=True, related_name='insurances')
    insurance_provider = models.ForeignKey(
        InsuranceProfile, 
        on_delete=models.PROTECT, # Prevents deleting a company that has policies
        related_name='policies'
    )
    insurance_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    policy_number = models.CharField(max_length=50, unique=True)
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPE_CHOICES)
    valid_from = models.DateField()
    valid_to = models.DateField()
    coverage_amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    policy_document = models.FileField(upload_to='insurance_documents/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if hasattr(self, 'patient') and self.patient:
            return f"{self.policy_number} - {self.patient.name}"
        else:
            # Provide a default string if no patient is linked yet
            return f"{self.policy_number} - (Unassigned)"