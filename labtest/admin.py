from django.contrib import admin
from .models import LabTest,LabStaffProfile

@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ['test_type', 'patient', 'doctor', 'status', 'test_date']

@admin.register(LabStaffProfile)
class LabStaffProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'phone', 'email', 'clinic']