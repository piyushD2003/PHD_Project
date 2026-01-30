from .models import Clinic

def get_default_clinic():
    return Clinic.objects.first()  # or filter(is_default=True).first() if using a flag
