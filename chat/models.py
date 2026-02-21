
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
import uuid
from io import BytesIO
from django.conf import settings

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', default='default-avatar.jpg')
    status = models.CharField(max_length=255, default='Available')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_avatar_url(self):
        # Check if avatar is default or doesn't exist
        if self.avatar and self.avatar.name and self.avatar.name != 'default-avatar.jpg':
            return self.avatar.url
        # Always return static default avatar
        return f"{settings.STATIC_URL}images/default-avatar.jpg"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=UserProfile)
def resize_avatar(sender, instance, **kwargs):
    if instance.avatar and instance.avatar.name != 'default-avatar.jpg':
        try:
            img = Image.open(instance.avatar.path)
            if img.width > 100 or img.height > 100:
                output_size = (100, 100)
                img.thumbnail(output_size)
                img.save(instance.avatar.path)
        except Exception as e:
            print(f"Error resizing avatar: {e}")

class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    members = models.ManyToManyField(User, related_name='rooms')
    is_group = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()  # Encrypted content
    is_media = models.BooleanField(default=False)
    media_file = models.FileField(upload_to='messages/%Y/%m/%d/', null=True, blank=True)
    media_thumbnail = models.ImageField(upload_to='thumbnails/%Y/%m/%d/', null=True, blank=True)
    preview = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username} - {self.room.name}"

    def save(self, *args, **kwargs):
        self.preview = self.content[:100]
        super().save(*args, **kwargs)

class UserSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    device_name = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-last_active']

    def __str__(self):
        return f"{self.user.username} - {self.device_name}"
