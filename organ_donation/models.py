from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from patient.models import PatientProfile
from doctor.models import DoctorProfile


class OrganType(models.Model):
    """Types of organs that can be donated"""
    ORGAN_CHOICES = [
        ('heart', 'Heart'),
        ('kidney', 'Kidney'),
        ('liver', 'Liver'),
        ('lung', 'Lung'),
        ('pancreas', 'Pancreas'),
        ('cornea', 'Cornea'),
        ('bone_marrow', 'Bone Marrow'),
        ('blood', 'Blood'),
        ('tissue', 'Tissue'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=50, choices=ORGAN_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.get_name_display()
    
    class Meta:
        ordering = ['name']


class BloodType(models.Model):
    """Blood type compatibility for organ matching"""
    BLOOD_CHOICES = [
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
    ]
    
    blood_type = models.CharField(max_length=3, choices=BLOOD_CHOICES, unique=True)
    
    def __str__(self):
        return self.blood_type
    
    class Meta:
        ordering = ['blood_type']


class OrganDonation(models.Model):
    """Model for organ donations - tracks organs available for donation"""
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('matched', 'Matched'),
        ('engaged', 'Engaged'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    donor = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='organ_donations')
    organ_type = models.ForeignKey(OrganType, on_delete=models.SET_NULL, null=True)
    blood_type = models.ForeignKey(BloodType, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    
    # Medical information
    health_condition = models.TextField(help_text="Current health condition and any relevant medical history")
    age_at_donation = models.IntegerField()
    
    # Donation details
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    available_from = models.DateTimeField(default=timezone.now)
    
    # Matching information
    matched_request = models.OneToOneField('OrganRequest', on_delete=models.SET_NULL, 
                                           null=True, blank=True, related_name='donation_matched_with')
    
    notes = models.TextField(blank=True, null=True, help_text="Additional medical notes")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'organ_type']),
            models.Index(fields=['donor', 'status']),
        ]
    
    def __str__(self):
        return f"{self.donor.user.get_full_name()} - {self.organ_type} ({self.status})"
    
    def clean(self):
        """Validation logic for organ donation"""
        if self.age_at_donation < 18:
            raise ValidationError("Donor must be at least 18 years old")
    
    def can_be_matched(self):
        """Check if donation can be matched with a request"""
        return self.status == 'available' and self.matched_request is None
    
    def match_with_request(self, organ_request):
        """Match this donation with a request and lock it"""
        if not self.can_be_matched():
            raise ValidationError("This donation cannot be matched")
        
        self.status = 'matched'
        self.matched_request = organ_request
        self.save()
    
    def complete_donation(self):
        """Mark donation as completed"""
        self.status = 'completed'
        self.save()
    
    def engage_donation(self):
        """Mark donation as engaged (contact initiated with recipient)"""
        self.status = 'engaged'
        self.save()
    
    def cancel_donation(self):
        """Cancel the donation"""
        self.status = 'cancelled'
        self.matched_request = None
        self.save()


class OrganRequest(models.Model):
    """Model for organ requests - tracks organs needed by patients"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('engaged', 'Engaged'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    URGENCY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    requester = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='organ_requests')
    organ_type = models.ForeignKey(OrganType, on_delete=models.SET_NULL, null=True)
    blood_type = models.ForeignKey(BloodType, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='medium')
    
    # Medical information
    medical_condition = models.TextField(help_text="Current medical condition and why organ is needed")
    age_at_request = models.IntegerField()
    
    # Request timeline
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    needed_by = models.DateTimeField(null=True, blank=True, help_text="Date by which organ is needed")
    
    # Matching information
    matched_donation = models.OneToOneField(OrganDonation, on_delete=models.SET_NULL,
                                           null=True, blank=True, related_name='request_matched_with')
    
    notes = models.TextField(blank=True, null=True, help_text="Additional medical notes")
    
    class Meta:
        ordering = ['-urgency', '-created_at']
        indexes = [
            models.Index(fields=['status', 'organ_type']),
            models.Index(fields=['requester', 'status']),
            models.Index(fields=['urgency', 'status']),
        ]
    
    def __str__(self):
        return f"{self.requester.user.get_full_name()} - {self.organ_type} ({self.status})"
    
    def clean(self):
        """Validation logic for organ request"""
        if self.age_at_request < 0:
            raise ValidationError("Age cannot be negative")
        
        # Prevent self-matching
        if hasattr(self, 'matched_donation') and self.matched_donation:
            if self.matched_donation.donor == self.requester:
                raise ValidationError("Cannot request own donated organs")
    
    def can_be_matched(self):
        """Check if request can be matched with a donation"""
        return self.status == 'pending' and self.matched_donation is None
    
    def accept_donation(self, donation):
        """Accept a donation for this request"""
        if not self.can_be_matched():
            raise ValidationError("This request cannot accept a donation")
        
        if donation.status != 'available':
            raise ValidationError("This donation is not available")
        
        # Check blood type compatibility (basic check)
        if donation.blood_type and self.blood_type:
            if not self._is_compatible(donation.blood_type.blood_type, self.blood_type.blood_type):
                raise ValidationError("Blood types are not compatible")
        
        self.status = 'accepted'
        self.matched_donation = donation
        self.save()
        
        # Update donation status
        donation.status = 'matched'
        donation.matched_request = self
        donation.save()
    
    def reject_request(self):
        """Reject the request"""
        self.status = 'rejected'
        self.matched_donation = None
        self.save()
    
    def complete_request(self):
        """Mark request as completed (after organ transplant)"""
        self.status = 'completed'
        self.save()
        
        if self.matched_donation:
            self.matched_donation.complete_donation()
    
    def engage_request(self):
        """Mark request as engaged (contact initiated with donor)"""
        self.status = 'engaged'
        self.save()
    
    def cancel_request(self):
        """Cancel the request"""
        self.status = 'cancelled'
        self.matched_donation = None
        self.save()
    
    @staticmethod
    def _is_compatible(donor_blood, recipient_blood):
        """
        Check blood type compatibility for organ donation.
        Universal donor: O-
        Universal recipient: AB+
        """
        compatibility_matrix = {
            'O+': ['O+', 'A+', 'B+', 'AB+'],
            'O-': ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-'],
            'A+': ['A+', 'AB+'],
            'A-': ['A+', 'A-', 'AB+', 'AB-'],
            'B+': ['B+', 'AB+'],
            'B-': ['B+', 'B-', 'AB+', 'AB-'],
            'AB+': ['AB+'],
            'AB-': ['AB+', 'AB-'],
        }
        return recipient_blood in compatibility_matrix.get(donor_blood, [])


class DoctorApproval(models.Model):
    """Model to track doctor approvals for organ matching"""
    APPROVAL_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    donation = models.ForeignKey(OrganDonation, on_delete=models.CASCADE, related_name='doctor_approvals')
    request = models.ForeignKey(OrganRequest, on_delete=models.CASCADE, related_name='doctor_approvals')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default='pending')
    
    approval_date = models.DateTimeField(null=True, blank=True)
    reason = models.TextField(blank=True, null=True, help_text="Reason for approval/rejection")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['donation', 'request', 'doctor']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Approval: {self.donation.organ_type} - {self.status}"
    
    def approve(self, reason=""):
        """Approve the organ matching"""
        self.status = 'approved'
        self.approval_date = timezone.now()
        self.reason = reason
        self.save()
    
    def reject(self, reason=""):
        """Reject the organ matching"""
        self.status = 'rejected'
        self.reason = reason
        self.save()


class OrganTransaction(models.Model):
    """Model to track completed organ donation transactions"""
    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    donation = models.OneToOneField(OrganDonation, on_delete=models.SET_NULL, null=True, related_name='transaction')
    request = models.OneToOneField(OrganRequest, on_delete=models.SET_NULL, null=True, related_name='transaction')
    
    donor = models.ForeignKey(PatientProfile, on_delete=models.SET_NULL, null=True, related_name='donated_transactions')
    recipient = models.ForeignKey(PatientProfile, on_delete=models.SET_NULL, null=True, related_name='received_transactions')
    
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='pending')
    organ_type = models.ForeignKey(OrganType, on_delete=models.SET_NULL, null=True)
    
    # Assigned doctor
    assigned_doctor = models.ForeignKey(DoctorProfile, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Transaction timeline
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Transaction details
    notes = models.TextField(blank=True, null=True, help_text="Transaction notes and outcomes")
    success_rate = models.FloatField(default=0.0, help_text="Estimated or actual success rate")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'donor']),
            models.Index(fields=['status', 'recipient']),
        ]
    
    def __str__(self):
        return f"Transaction: {self.donor} -> {self.recipient} ({self.organ_type})"
    
    def complete_transaction(self):
        """Mark transaction as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Update related donation and request
        if self.donation:
            self.donation.complete_donation()
        if self.request:
            self.request.complete_request()
