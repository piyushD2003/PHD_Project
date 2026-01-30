from django.contrib import admin
from .models import (
    OrganType, BloodType, OrganDonation, OrganRequest,
    DoctorApproval, OrganTransaction
)


@admin.register(OrganType)
class OrganTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(BloodType)
class BloodTypeAdmin(admin.ModelAdmin):
    list_display = ['blood_type']


@admin.register(OrganDonation)
class OrganDonationAdmin(admin.ModelAdmin):
    list_display = ['id', 'donor', 'organ_type', 'blood_type', 'status', 'created_at']
    list_filter = ['status', 'organ_type', 'created_at']
    search_fields = ['donor__user__username', 'donor__user__first_name', 'donor__user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'id']
    
    fieldsets = (
        ('Donor Information', {
            'fields': ('donor', 'age_at_donation')
        }),
        ('Organ Details', {
            'fields': ('organ_type', 'blood_type', 'health_condition', 'notes')
        }),
        ('Status', {
            'fields': ('status', 'matched_request', 'available_from')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrganRequest)
class OrganRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'requester', 'organ_type', 'blood_type', 'urgency', 'status', 'created_at']
    list_filter = ['status', 'urgency', 'organ_type', 'created_at']
    search_fields = ['requester__user__username', 'requester__user__first_name', 'requester__user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'id']
    
    fieldsets = (
        ('Requester Information', {
            'fields': ('requester', 'age_at_request')
        }),
        ('Organ Details', {
            'fields': ('organ_type', 'blood_type', 'medical_condition', 'notes')
        }),
        ('Status & Urgency', {
            'fields': ('status', 'urgency', 'needed_by', 'matched_donation')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DoctorApproval)
class DoctorApprovalAdmin(admin.ModelAdmin):
    list_display = ['id', 'donation', 'request', 'doctor', 'status', 'approval_date']
    list_filter = ['status', 'created_at', 'doctor']
    search_fields = ['doctor__user__username', 'donation__donor__user__username']
    readonly_fields = ['created_at', 'updated_at', 'id']
    
    fieldsets = (
        ('Match Information', {
            'fields': ('donation', 'request', 'doctor')
        }),
        ('Approval Details', {
            'fields': ('status', 'reason', 'approval_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrganTransaction)
class OrganTransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'organ_type', 'donor', 'recipient', 'status', 'assigned_doctor', 'completed_at']
    list_filter = ['status', 'created_at', 'organ_type', 'assigned_doctor']
    search_fields = ['donor__user__username', 'recipient__user__username', 'assigned_doctor__user__username']
    readonly_fields = ['created_at', 'updated_at', 'id']
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('donation', 'request', 'organ_type')
        }),
        ('Parties Involved', {
            'fields': ('donor', 'recipient', 'assigned_doctor')
        }),
        ('Status & Details', {
            'fields': ('status', 'notes', 'success_rate', 'completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
