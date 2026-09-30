"""
Management command to create sample data for demo/hackathon
Run: python manage.py create_sample_data
"""
from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from user_app.models import Complaint, PickupRequest, Awareness
from datetime import date, time, timedelta


class Command(BaseCommand):
    help = 'Creates sample data for the Smart Waste Management System demo'

    def handle(self, *args, **kwargs):
        self.stdout.write('>>> Creating sample data...\n')

        # 1. Admin User
        admin, _ = CustomUser.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@ecocity.gov',
                'first_name': 'Municipal',
                'last_name': 'Admin',
                'role': 'admin',
                'is_staff': True,
                'phone': '+91 98765 00001',
            }
        )
        admin.set_password('admin123')
        admin.save()
        self.stdout.write(self.style.SUCCESS('  [OK] Admin -> username: admin | password: admin123'))

        # 2. Collectors
        collector1, _ = CustomUser.objects.get_or_create(
            username='collector1',
            defaults={
                'email': 'collector1@ecocity.gov',
                'first_name': 'Raju',
                'last_name': 'Sharma',
                'role': 'collector',
                'phone': '+91 98765 11111',
                'zone': 'Zone A - North City',
            }
        )
        collector1.set_password('collector123')
        collector1.save()

        collector2, _ = CustomUser.objects.get_or_create(
            username='collector2',
            defaults={
                'email': 'collector2@ecocity.gov',
                'first_name': 'Priya',
                'last_name': 'Patel',
                'role': 'collector',
                'phone': '+91 98765 22222',
                'zone': 'Zone B - South City',
            }
        )
        collector2.set_password('collector123')
        collector2.save()
        self.stdout.write(self.style.SUCCESS('  [OK] Collectors -> collector1, collector2 | password: collector123'))

        # 3. Citizens
        citizen1, _ = CustomUser.objects.get_or_create(
            username='citizen1',
            defaults={
                'email': 'citizen1@gmail.com',
                'first_name': 'Amit',
                'last_name': 'Kumar',
                'role': 'citizen',
                'phone': '+91 98765 33333',
                'address': '45 MG Road, North City',
            }
        )
        citizen1.set_password('citizen123')
        citizen1.save()

        citizen2, _ = CustomUser.objects.get_or_create(
            username='citizen2',
            defaults={
                'email': 'citizen2@gmail.com',
                'first_name': 'Sunita',
                'last_name': 'Rao',
                'role': 'citizen',
                'phone': '+91 98765 44444',
                'address': '12 Park Street, South City',
            }
        )
        citizen2.set_password('citizen123')
        citizen2.save()
        self.stdout.write(self.style.SUCCESS('  [OK] Citizens -> citizen1, citizen2 | password: citizen123'))

        # 4. Complaints
        complaints_data = [
            {
                'title': 'Overflowing bin near MG Road bus stop',
                'issue_type': 'overflowing_bin',
                'description': 'The garbage bin at the MG Road bus stop has been overflowing for 3 days. Waste is spilling on the road causing bad smell.',
                'location_address': 'MG Road Bus Stop, North City',
                'latitude': 28.6139,
                'longitude': 77.2090,
                'status': 'pending',
                'reported_by': citizen1,
            },
            {
                'title': 'Garbage dumped on Park Street footpath',
                'issue_type': 'garbage_on_road',
                'description': 'Someone has illegally dumped a large pile of construction debris on the footpath near Park Street.',
                'location_address': 'Park Street, South City',
                'latitude': 28.5245,
                'longitude': 77.1855,
                'status': 'in_progress',
                'reported_by': citizen2,
                'assigned_to': collector2,
            },
            {
                'title': 'Missed weekly collection - Sector 14',
                'issue_type': 'missed_collection',
                'description': 'The garbage truck has not come to Sector 14 for the past two weeks. Waste is piling up outside every house.',
                'location_address': 'Sector 14, West Zone',
                'latitude': 28.6500,
                'longitude': 77.1500,
                'status': 'resolved',
                'reported_by': citizen1,
                'assigned_to': collector1,
                'admin_notes': 'Collection team deployed. Issue resolved on 28 Sep 2024.',
            },
            {
                'title': 'Illegal dumping near railway tracks',
                'issue_type': 'illegal_dumping',
                'description': 'A truck was spotted dumping chemical waste near the old railway tracks. This is a serious environmental hazard.',
                'location_address': 'Old Railway Track, East End',
                'latitude': 28.6800,
                'longitude': 77.2500,
                'status': 'pending',
                'reported_by': citizen2,
            },
            {
                'title': 'Broken bin at Central Market',
                'issue_type': 'overflowing_bin',
                'description': 'The garbage bin at Central Market is broken and waste is scattered all around the area.',
                'location_address': 'Central Market, Main Square',
                'latitude': 28.6350,
                'longitude': 77.2200,
                'status': 'in_progress',
                'reported_by': citizen1,
                'assigned_to': collector1,
            },
        ]

        for data in complaints_data:
            Complaint.objects.get_or_create(
                title=data['title'],
                defaults=data
            )

        self.stdout.write(self.style.SUCCESS(f'  [OK] {len(complaints_data)} complaints created'))

        # 5. Pickup Requests
        pickups_data = [
            {
                'waste_type': 'recyclable',
                'description': 'Old newspapers, plastic bottles and cardboard boxes',
                'preferred_date': date.today() + timedelta(days=1),
                'preferred_time': time(9, 0),
                'address': '45 MG Road, North City',
                'status': 'pending',
                'requested_by': citizen1,
            },
            {
                'waste_type': 'e_waste',
                'description': 'Old laptop, broken TV, and 3 mobile phones',
                'preferred_date': date.today() + timedelta(days=2),
                'preferred_time': time(11, 0),
                'address': '12 Park Street, South City',
                'status': 'accepted',
                'requested_by': citizen2,
                'assigned_to': collector2,
            },
            {
                'waste_type': 'bulk',
                'description': 'Old sofa, mattress, and wooden furniture after renovation',
                'preferred_date': date.today(),
                'preferred_time': time(14, 0),
                'address': '45 MG Road, North City',
                'status': 'on_the_way',
                'requested_by': citizen1,
                'assigned_to': collector1,
            },
        ]

        for data in pickups_data:
            PickupRequest.objects.get_or_create(
                waste_type=data['waste_type'],
                requested_by=data['requested_by'],
                defaults=data
            )

        self.stdout.write(self.style.SUCCESS(f'  [OK] {len(pickups_data)} pickup requests created'))

        # 6. Awareness Tips
        tips = [
            {
                'title': 'Segregate Your Waste Daily',
                'category': 'tip',
                'icon': 'R',
                'content': 'Always separate dry waste (paper, plastic, metal, glass) from wet waste (food scraps, vegetable peels). Use two separate dustbins at home.',
            },
            {
                'title': 'Start Home Composting',
                'category': 'composting',
                'icon': 'C',
                'content': 'Turn your kitchen waste into gold! Collect fruit peels, vegetable scraps, tea bags in a compost bin. In 6-8 weeks, you get rich natural fertilizer.',
            },
            {
                'title': 'Say No to Single-Use Plastics',
                'category': 'recycling',
                'icon': 'P',
                'content': 'Carry cloth bags for shopping, use steel water bottles. Single-use plastics take 400+ years to decompose and are the #1 ocean pollutant.',
            },
            {
                'title': 'Monthly Cleanliness Drive - October 2024',
                'category': 'announcement',
                'icon': 'A',
                'content': 'Municipal Corporation will conduct a city-wide cleanliness drive on October 5th, 2024. Place bulk waste outside by 8 AM.',
            },
            {
                'title': 'Proper E-Waste Disposal',
                'category': 'recycling',
                'icon': 'E',
                'content': 'Never throw old phones, laptops, batteries in regular bins. Use our E-Waste Pickup Request feature.',
            },
            {
                'title': 'Hazardous Waste - Handle with Care',
                'category': 'tip',
                'icon': 'H',
                'content': 'Paint cans, pesticides, and batteries are hazardous. Never pour them down drains or mix with regular trash.',
            },
        ]

        for tip_data in tips:
            tip_data['created_by'] = admin
            Awareness.objects.get_or_create(
                title=tip_data['title'],
                defaults=tip_data
            )

        self.stdout.write(self.style.SUCCESS(f'  [OK] {len(tips)} awareness tips created'))

        self.stdout.write('\n' + '='*55)
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!\n'))
        self.stdout.write('LOGIN CREDENTIALS:')
        self.stdout.write('  Admin     -> username: admin     | password: admin123')
        self.stdout.write('  Collector -> username: collector1 | password: collector123')
        self.stdout.write('  Citizen   -> username: citizen1   | password: citizen123')
        self.stdout.write('='*55 + '\n')
        self.stdout.write('Run: python manage.py runserver')
