
from django.urls import path
from . import views

urlpatterns = [
    path('', views.splash, name='splash'),
    path('qr-login/', views.qr_login, name='qr_login'),
    path('link/<uuid:session_id>/', views.link_device, name='link_device'),
    path('chat/', views.chat_view, name='chat'),
    path('logout/', views.logout_view, name='logout'),
    path('download/<uuid:message_id>/', views.download_message, name='download_message'),
    
    # API endpoints
    path('api/users/', views.get_all_users, name='get_users'),
    path('api/rooms/', views.get_user_rooms, name='get_rooms'),
    path('api/direct-message/<int:user_id>/', views.direct_message_room, name='direct_message'),
    path('api/create-group/', views.create_group, name='create_group'),
    
    # New WhatsApp API endpoints
    path('api/user-list/', views.user_list, name='user_list'),
    path('api/profile/', views.edit_profile, name='edit_profile'),
    path('api/room/<int:other_id>/', views.get_private_room, name='get_private_room'),
    path('api/room/<str:room_name>/messages/', views.get_room_messages, name='get_room_messages'),
    path('api/online-status/', views.set_online_status, name='set_online_status'),
]
