from django.contrib import admin
from .models import Medicine, MedicalProfile, Prescription, PrescriptionItem
admin.site.register(Medicine)
admin.site.register(MedicalProfile)
admin.site.register(Prescription)
admin.site.register(PrescriptionItem)
