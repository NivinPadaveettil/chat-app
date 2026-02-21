
from django.contrib import admin
from .models import Room, Message, UserSession

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_group', 'created_at')
    search_fields = ('name',)
    filter_horizontal = ('members',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'room', 'timestamp', 'is_media')
    search_fields = ('sender__username', 'room__name')
    list_filter = ('timestamp', 'is_media')

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_name', 'ip_address', 'created_at')
    search_fields = ('user__username', 'device_name')
    list_filter = ('created_at',)
