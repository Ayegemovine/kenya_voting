from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from voting.models import VoterProfile

class Command(BaseCommand):
    help = 'Deletes all dummy voters and profiles to start fresh'

    def handle(self, *args, **kwargs):
        # Filter for non-staff, non-superuser accounts to protect your admin
        voters = User.objects.filter(is_superuser=False, is_staff=False)
        count = voters.count()
        voters.delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully purged {count} dummy records.'))