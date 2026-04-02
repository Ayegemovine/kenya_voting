import random
import uuid
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from voting.models import VoterProfile
from django.db import transaction
from faker import Faker

class Command(BaseCommand):
    help = 'Purges existing data and populates 800,000 fresh unique voters'

    def handle(self, *args, **kwargs):
        fake = Faker()
        
        counties = [
            "Mombasa", "Kwale", "Kilifi", "Tana River", "Lamu", "Taita Taveta", 
            "Garissa", "Wajir", "Mandera", "Marsabit", "Isiolo", "Meru", 
            "Tharaka-Nithi", "Embu", "Kitui", "Machakos", "Makueni", "Nyandarua", 
            "Nyeri", "Kirinyaga", "Murang'a", "Kiambu", "Turkana", "West Pokot", 
            "Samburu", "Trans Nzoia", "Uasin Gishu", "Elgeyo-Marakwet", "Nandi", 
            "Baringo", "Laikipia", "Nakuru", "Narok", "Kajiado", "Kericho", 
            "Bomet", "Kakamega", "Vihiga", "Bungoma", "Busia", "Siaya", 
            "Kisumu", "Homa Bay", "Migori", "Kisii", "Nyamira", "Nairobi"
        ]

        # ── 1. BATCHED PURGE (Fixes "Too many SQL variables") ──
        self.stdout.write(self.style.WARNING('Purging existing dummy data in batches...'))
        
        # Get all non-admin IDs
        voter_ids = list(User.objects.filter(is_superuser=False, is_staff=False).values_list('id', flat=True))
        total_to_purge = len(voter_ids)
        
        # Delete in chunks of 500 to stay well below SQLite limits
        purge_batch = 500
        for i in range(0, total_to_purge, purge_batch):
            chunk = voter_ids[i:i + purge_batch]
            User.objects.filter(id__in=chunk).delete()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully purged {total_to_purge} records.'))

        # ── 2. BATCHED GENERATION ──
        total_voters = 800000
        gen_batch = 10000  
        
        self.stdout.write(self.style.MIGRATE_HEADING(f'🚀 Generating {total_voters} fresh records...'))

        for i in range(0, total_voters, gen_batch):
            with transaction.atomic():
                users_to_create = []
                profile_metadata = [] 

                for _ in range(gen_batch):
                    # Use UUID for absolute uniqueness
                    unique_suffix = uuid.uuid4().hex[:6]
                    f_name = fake.first_name()
                    l_name = fake.last_name()
                    uname = f"{f_name.lower()}.{l_name.lower()}.{unique_suffix}"
                    
                    user = User(
                        username=uname,
                        first_name=f_name,
                        last_name=l_name,
                        email=f"{uname}@vote-x.ke"
                    )
                    user.set_unusable_password()
                    users_to_create.append(user)
                    
                    profile_metadata.append({
                        # High-entropy random ID
                        'national_id': f"{random.randint(10000000, 99999999)}-{unique_suffix.upper()}", 
                        'county': random.choice(counties)
                    })

                # Step 1: Bulk create users
                created_users = User.objects.bulk_create(users_to_create)

                # Step 2: Prepare and Bulk create profiles
                profiles_to_create = [
                    VoterProfile(
                        user=user,
                        county=profile_metadata[idx]['county'],
                        national_id=profile_metadata[idx]['national_id'],
                        role='voter'
                    ) for idx, user in enumerate(created_users)
                ]
                
                VoterProfile.objects.bulk_create(profiles_to_create)

            self.stdout.write(f"Injected: {i + gen_batch} / {total_voters}")

        self.stdout.write(self.style.SUCCESS('🏁 RESET COMPLETE: 800,000 fresh voters added.'))