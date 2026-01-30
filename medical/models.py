from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
# from doctor.models import Clinic 
# from patient.models import PatientProfile
from billing.models import Billing

# The user profile for the pharmacy/medical staff
class MedicalProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='medical_profile')
    clinic = models.ForeignKey("doctor.Clinic", on_delete=models.CASCADE)
    email = models.EmailField(null=True, blank=True)
    pharmacy_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    address = models.TextField(default=None,blank=True, null=True)
    profile_pic = models.ImageField(upload_to='medical_profiles/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.pharmacy_name}"

class Medicine(models.Model):
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    strength = models.CharField(max_length=50) # e.g., "500mg"
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.brand}) - {self.strength}"

# The "header" for a prescription, linking doctor and patient.
class Prescription(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Dispensed', 'Dispensed'),
        ('Cancelled', 'Cancelled'),
    ]
    patient = models.ForeignKey('patient.PatientProfile', on_delete=models.CASCADE,null=True, blank=True, related_name='medicines')
    doctor = models.ForeignKey('doctor.DoctorProfile', on_delete=models.CASCADE, null=True, blank=True, related_name='medicines')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    # This links to the line items below
    medicines = models.ManyToManyField(Medicine, through='PrescriptionItem')

    def __str__(self):
        return f"Prescription for {self.patient.name} by Dr. {self.doctor.name} on {self.created_at.date()}"
    
    # This will be useful for billing
    def get_total_cost(self):
        total = 0
        for item in self.items.all():
            total += item.get_item_total()
        return total

# The individual "line items" of a prescription.
class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    instructions = models.CharField(max_length=255) # e.g., "Take 2 daily after meals"

    def __str__(self):
        return f"{self.quantity} x {self.medicine.name} for Prescription #{self.prescription.id}"
    
    # This will be useful for billing
    def get_item_total(self):
        return self.quantity * self.medicine.price_per_unit

# class Medicine(models.Model):
#     PRESCRIPTION_CHOICES = [
#         (True, 'Yes'),
#         (False, 'No'),
#     ]

#     medicine_name = models.CharField(max_length=255)
#     generic_name = models.CharField(max_length=255)
#     brand = models.CharField(max_length=255)
#     dosage = models.CharField(max_length=100)
#     frequency = models.CharField(max_length=100)
#     route = models.CharField(max_length=100)
#     side_effects = models.TextField(blank=True, null=True)
#     price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
#     is_prescription_required = models.BooleanField(choices=PRESCRIPTION_CHOICES, default=True)
    
#     doctor = models.ForeignKey(DoctorProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='medicines')
#     patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True, related_name='medicines')
#     billing = models.ForeignKey(Billing, on_delete=models.SET_NULL, null=True, blank=True, related_name='medicines')
#     clinic = models.ForeignKey(Clinic, on_delete=models.SET_NULL, null=True, blank=True, related_name='medicines')

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.medicine_name} ({self.brand})"


