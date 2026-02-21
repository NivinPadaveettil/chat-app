from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import logout as auth_logout
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.middleware.csrf import get_token
import qrcode
import uuid as uuid_lib
import os
from django.conf import settings
from .models import Room, Message, UserSession, UserProfile

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def splash(request):
    if request.user.is_authenticated:
        return redirect('chat')
    return render(request, 'splash.html')

@require_http_methods(["GET"])
def qr_login(request):
    session_uuid = uuid_lib.uuid4()
    
    # Get host info
    host = request.META.get('HTTP_HOST', 'localhost:8000')
    protocol = 'https' if request.is_secure() else 'http'
    qr_link = f"{protocol}://{host}/link/{session_uuid}/"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_link)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR
    os.makedirs(f"{settings.MEDIA_ROOT}/qr", exist_ok=True)
    qr_path = f"{settings.MEDIA_ROOT}/qr/{session_uuid}.png"
    img.save(qr_path)
    
    return JsonResponse({
        'qr_url': f"/media/qr/{session_uuid}.png",
        'session_id': str(session_uuid),
        'link': qr_link,
    })

@require_http_methods(["GET", "POST"])
def link_device(request, session_id):
    if request.method == "POST":
        username = request.POST.get('username', f'user_{uuid_lib.uuid4().hex[:8]}')
        device_name = request.POST.get('device_name', 'Mobile Device')
        
        user, created = User.objects.get_or_create(username=username)
        
        ip_address = get_client_ip(request)
        UserSession.objects.create(
            user=user,
            device_name=device_name,
            ip_address=ip_address
        )
        
        login(request, user)
        return redirect('chat')
    
    return render(request, 'login.html', {'session_id': session_id})

@require_http_methods(["GET"])
def chat_view(request):
    if not request.user.is_authenticated:
        return redirect('splash')
    
    rooms = request.user.rooms.all()
    messages = Message.objects.all()[:50]
    
    context = {
        'rooms': rooms,
        'messages': messages,
        'user': request.user,
    }
    
    return render(request, 'chat.html', context)

@require_http_methods(["GET"])
@require_http_methods(["GET"])
def logout_view(request):
    """
    Logout and completely remove user from system
    - Delete all user sessions
    - Delete all user messages
    - Delete user from rooms
    - Delete user account
    """
    if request.user.is_authenticated:
        user = request.user
        username = user.username
        
        # Delete all user sessions
        from .models import UserSession
        UserSession.objects.filter(user=user).delete()
        
        # Delete user account (cascades: sessions, messages, room memberships)
        user.delete()
        
        print(f"✅ User '{username}' completely removed from system")
    
    # Logout session
    auth_logout(request)
    return redirect('splash')

# API Endpoints for frontend

@require_http_methods(["GET"])
def get_all_users(request):
    """Get all users except current user"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    users = User.objects.exclude(id=request.user.id).values('id', 'username', 'email')
    return JsonResponse({
        'users': list(users),
        'total': users.count()
    })

@require_http_methods(["GET"])
def get_user_rooms(request):
    """Get all rooms/chats for current user"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    rooms = request.user.rooms.all()
    room_list = []
    
    for room in rooms:
        # Get other members for direct message rooms
        other_members = room.members.exclude(id=request.user.id)
        
        # Get last message
        last_message = room.messages.last()
        
        room_list.append({
            'id': str(room.id),
            'name': room.name,
            'is_group': room.is_group,
            'members': [m.username for m in room.members.all()],
            'member_count': room.members.count(),
            'last_message': last_message.content if last_message else 'No messages yet',
            'last_message_time': str(last_message.timestamp) if last_message else None,
        })
    
    return JsonResponse({'rooms': room_list})

@require_http_methods(["GET", "POST"])
def direct_message_room(request, user_id):
    """Get or create direct message room with another user"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    other_user = get_object_or_404(User, id=user_id)
    
    if other_user.id == request.user.id:
        return JsonResponse({'error': 'Cannot message yourself'}, status=400)
    
    # Try to find existing room
    existing_rooms = request.user.rooms.filter(is_group=False)
    room = None
    
    for r in existing_rooms:
        if r.members.count() == 2 and r.members.filter(id=other_user.id).exists():
            room = r
            break
    
    # Create new room if not found
    if not room:
        # Sort usernames to ensure consistent room name regardless of who initiates
        usernames = sorted([request.user.username, other_user.username])
        room_name = f"{usernames[0]}__{usernames[1]}"
        room, created = Room.objects.get_or_create(
            name=room_name,
            defaults={'is_group': False}
        )
        room.members.add(request.user, other_user)
    
    return JsonResponse({
        'room_id': str(room.id),
        'room_name': room.name,
        'is_group': room.is_group,
        'members': [m.username for m in room.members.all()],
    })

@require_http_methods(["POST"])
def create_group(request):
    """Create a new group chat"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        import json
        data = json.loads(request.body)
        group_name = data.get('group_name', 'New Group')
        member_ids = data.get('member_ids', [])
        
        # Ensure current user is included
        if request.user.id not in member_ids:
            member_ids.append(request.user.id)
        
        # Create unique group name
        timestamp = uuid_lib.uuid4().hex[:6]
        unique_name = f"{group_name}_{timestamp}"
        
        room = Room.objects.create(
            name=unique_name,
            is_group=True
        )
        
        # Add members
        members = User.objects.filter(id__in=member_ids)
        room.members.set(members)
        
        return JsonResponse({
            'room_id': str(room.id),
            'room_name': room.name,
            'is_group': True,
            'members': [m.username for m in room.members.all()],
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(["GET"])
def download_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    
    if message.room.members.filter(id=request.user.id).exists():
        if message.media_file:
            return FileResponse(
                open(message.media_file.path, 'rb'),
                as_attachment=True,
                filename=os.path.basename(message.media_file.path)
            )
    
    return JsonResponse({'error': 'Unauthorized'}, status=403)

# New WhatsApp Clone API Endpoints

@require_http_methods(["GET"])
def user_list(request):
    """Get all users with profile info, last message, online status"""
    print(f"[user_list] Request from {request.remote_addr if hasattr(request, 'remote_addr') else 'unknown'}")
    print(f"[user_list] User authenticated: {request.user.is_authenticated}")
    print(f"[user_list] User: {request.user}")
    print(f"[user_list] Session key: {request.session.session_key}")
    
    if not request.user.is_authenticated:
        print(f"[user_list] Returning 401 Unauthorized")
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    print(f"[user_list] Loading users list for user: {request.user.username}")
    users = []
    all_users = User.objects.exclude(id=request.user.id)
    
    for user in all_users:
        try:
            profile = user.profile
        except:
            profile = UserProfile.objects.create(user=user)
        
        # Get last message between current user and this user
        last_message = Message.objects.filter(
            room__members__in=[request.user, user]
        ).order_by('-timestamp').first()
        
        users.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'avatar': profile.get_avatar_url(),
            'status': profile.status,
            'is_online': profile.is_online,
            'last_message': last_message.preview if last_message else 'No messages',
            'last_message_time': str(last_message.timestamp) if last_message else None,
        })
    
    return JsonResponse({'users': users})

@require_http_methods(["GET", "POST"])
def edit_profile(request):
    """Edit user profile (status and avatar)"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    if request.method == 'POST':
        try:
            profile = request.user.profile
        except:
            profile = UserProfile.objects.create(user=request.user)
        
        status = request.POST.get('status')
        avatar = request.FILES.get('avatar')
        
        if status:
            profile.status = status
        
        if avatar:
            profile.avatar = avatar
        
        profile.save()
        
        return JsonResponse({
            'success': True,
            'avatar': profile.get_avatar_url(),
            'status': profile.status,
        })
    
    profile = request.user.profile if hasattr(request.user, 'profile') else UserProfile.objects.create(user=request.user)
    
    return JsonResponse({
        'username': request.user.username,
        'email': request.user.email,
        'avatar': profile.get_avatar_url(),
        'status': profile.status,
    })

@require_http_methods(["GET", "POST"])
def get_private_room(request, other_id):
    """Get or create private room with another user"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    other_user = get_object_or_404(User, id=other_id)
    
    if other_user.id == request.user.id:
        return JsonResponse({'error': 'Cannot message yourself'}, status=400)
    
    # Create room name with sorted IDs   
    room_name = f"{min(request.user.id, other_user.id)}_{max(request.user.id, other_user.id)}"
    room, created = Room.objects.get_or_create(name=room_name, defaults={'is_group': False})
    
    if created:
        room.members.add(request.user, other_user)
    else:
        room.members.add(request.user, other_user)
    
    return JsonResponse({
        'room_name': room_name,
        'other_user_id': other_user.id,
        'other_username': other_user.username,
    })

@require_http_methods(["GET"])
def get_room_messages(request, room_name):
    """Get last 50 messages from a room"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    room = get_object_or_404(Room, name=room_name)
    messages = room.messages.all().order_by('-timestamp')[:50]
    
    messages_data = []
    for msg in reversed(messages):
        try:
            sender_profile = msg.sender.profile
        except:
            sender_profile = UserProfile.objects.create(user=msg.sender)
        
        messages_data.append({
            'id': str(msg.id),
            'sender': msg.sender.username,
            'sender_id': msg.sender.id,
            'avatar': sender_profile.get_avatar_url(),
            'content': msg.content,
            'is_media': msg.is_media,
            'media_file': msg.media_file.url if msg.media_file else None,
            'timestamp': str(msg.timestamp),
        })
    
    return JsonResponse({'messages': messages_data})

@csrf_exempt
@require_http_methods(["POST"])
def set_online_status(request):
    """Set user online/offline status"""
    print(f"[set_online_status] User: {request.user}, Authenticated: {request.user.is_authenticated}")
    
    if not request.user.is_authenticated:
        print(f"[set_online_status] User not authenticated, returning 401")
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        import json
        data = json.loads(request.body)
        is_online = data.get('is_online', False)
        print(f"[set_online_status] Setting is_online={is_online} for user {request.user.username}")
        
        try:
            profile = request.user.profile
        except:
            profile = UserProfile.objects.create(user=request.user)
        
        profile.is_online = is_online
        profile.save()
        
        print(f"[set_online_status] Success - is_online now: {profile.is_online}")
        return JsonResponse({'success': True, 'is_online': is_online})
    except Exception as e:
        print(f"[set_online_status] Error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
