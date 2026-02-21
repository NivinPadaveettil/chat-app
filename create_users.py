import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inderbara.settings')
import django
django.setup()

from django.contrib.auth.models import User

# Delete existing admin user
User.objects.filter(username='admin').delete()

# Create new admin user
admin = User.objects.create_superuser('admin', 'admin@inderbara.com', 'admin123456')
print(f'✅ Admin user created: {admin.username}')

# Create a few test users
test_users = ['alice', 'bob', 'charlie']
for username in test_users:
    User.objects.filter(username=username).delete()
    user = User.objects.create_user(username, f'{username}@inderbara.com', 'password123')
    print(f'✅ Test user created: {user.username}')

print(f'\n📊 Total users: {User.objects.count()}')
print('\nCredentials:')
print('Admin: admin / admin123456')
print('Test users: alice, bob, charlie (all with password: password123)')
