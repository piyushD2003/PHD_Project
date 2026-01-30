from django.core.management.base import BaseCommand
from organ_donation.models import OrganType, BloodType


class Command(BaseCommand):
    help = 'Populate organ types and blood types in the database'

    def handle(self, *args, **options):
        # Organ types
        organ_data = [
            {'name': 'heart', 'description': 'Heart for transplantation'},
            {'name': 'kidney', 'description': 'Kidney for transplantation'},
            {'name': 'liver', 'description': 'Liver for transplantation'},
            {'name': 'lung', 'description': 'Lung for transplantation'},
            {'name': 'pancreas', 'description': 'Pancreas for transplantation'},
            {'name': 'cornea', 'description': 'Cornea for eye transplantation'},
            {'name': 'bone_marrow', 'description': 'Bone marrow for transplantation'},
            {'name': 'blood', 'description': 'Blood for transfusion'},
            {'name': 'tissue', 'description': 'Tissue for transplantation'},
            {'name': 'other', 'description': 'Other organs or tissues'},
        ]

        for organ in organ_data:
            obj, created = OrganType.objects.get_or_create(
                name=organ['name'],
                defaults={'description': organ['description']}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created organ type: {organ["name"]}')
                )
            else:
                self.stdout.write(f'Organ type already exists: {organ["name"]}')

        # Blood types
        blood_types = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']

        for blood_type in blood_types:
            obj, created = BloodType.objects.get_or_create(blood_type=blood_type)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created blood type: {blood_type}')
                )
            else:
                self.stdout.write(f'Blood type already exists: {blood_type}')

        self.stdout.write(
            self.style.SUCCESS('Successfully populated organ types and blood types!')
        )
