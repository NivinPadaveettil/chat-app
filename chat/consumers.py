
import json
import base64
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Room, Message, UserProfile
from PIL import Image
from io import BytesIO
import os
from django.conf import settings

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']

        print(f"\n{'='*80}")
        print(f"[CONNECT] User: {self.user.username} (ID: {self.user.id})")
        print(f"[CONNECT] Room: {self.room_name} → Group: {self.room_group_name}")
        print(f"{'='*80}\n")

        # Set user online
        if self.user.is_authenticated:
            await self.set_user_online(True)
            
            # IMPORTANT: Add user to room members immediately on connect
            room = await self.get_room(self.room_name)
            print(f"✅ User {self.user.username} added to room members")

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"✅ {self.user.username} joined {self.room_group_name}\n")

    async def disconnect(self, close_code):
        # Set user offline
        if self.user.is_authenticated:
            await self.set_user_online(False)
            
            # Broadcast user offline
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user.status',
                    'sender': self.user.username,
                    'is_online': False,
                }
            )
        
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'chat_message')

        if message_type == 'chat_message':
            await self.handle_chat_message(data)
        elif message_type == 'media_message':
            await self.handle_media_message(data)
        elif message_type == 'typing':
            await self.handle_typing(data)
        elif message_type == 'user_status':
            await self.handle_user_status(data)

    async def handle_chat_message(self, data):
        content = data.get('message', '')
        message_id = data.get('message_id', '')
        room = await self.get_room(self.room_name)

        message = await self.save_message(
            room=room,
            sender=self.user,
            content=content,
            is_media=False
        )

        sender_profile = await self.get_user_profile(self.user)

        print(f"\n{'='*80}")
        print(f"[MSG SAVED TO DB] Message ID: {str(message.id)}")
        print(f"[MSG SAVED TO DB] Room: {self.room_name}")
        print(f"[MSG SAVED TO DB] Sender: {self.user.username} (ID: {self.user.id})")
        print(f"[MSG SAVED TO DB] Content: {content[:60]}")
        print(f"{'='*80}")
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'content': content,
                'sender': self.user.username,
                'sender_id': self.user.id,
                'avatar': sender_profile.get_avatar_url() if sender_profile else '',
                'timestamp': str(message.timestamp),
                'message_id': message_id,
                'id': str(message.id),
                'is_media': False,
            }
        )
        print(f"✅ Broadcast to group: {self.room_group_name}\n")

    async def handle_media_message(self, data):
        filename = data.get('filename', 'file')
        file_data = data.get('file_data')
        is_image = data.get('is_image', False)
        message_id = data.get('message_id', '')

        if not file_data:
            return

        try:
            file_bytes = base64.b64decode(file_data.split(',')[-1])
            room = await self.get_room(self.room_name)

            thumbnail_path = None
            if is_image:
                thumbnail_path = await self.create_thumbnail(file_bytes, filename)

            file_path = await self.save_file(file_bytes, filename, room)

            message = await self.save_message(
                room=room,
                sender=self.user,
                content=f"Shared: {filename}",
                is_media=True,
                media_file=file_path,
                media_thumbnail=thumbnail_path
            )

            sender_profile = await self.get_user_profile(self.user)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'media.message',
                    'content': f"Shared: {filename}",
                    'sender': self.user.username,
                    'sender_id': self.user.id,
                    'avatar': sender_profile.get_avatar_url() if sender_profile else '',
                    'media_file': f"/media/{file_path}",
                    'thumbnail_url': f"/media/{thumbnail_path}" if thumbnail_path else None,
                    'filename': filename,
                    'timestamp': str(message.timestamp),
                    'message_id': message_id,
                    'id': str(message.id),
                    'is_media': True,
                }
            )
        except Exception as e:
            print(f"Error handling media: {e}")

    async def handle_typing(self, data):
        is_typing = data.get('is_typing', False)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing.indicator',
                'sender': self.user.username,
                'sender_id': self.user.id,
                'is_typing': is_typing,
            }
        )

    async def handle_user_status(self, data):
        is_online = data.get('is_online', False)
        await self.set_user_online(is_online)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user.status',
                'sender': self.user.username,
                'sender_id': self.user.id,
                'is_online': is_online,
            }
        )

    async def chat_message(self, event):
        print(f"[DELIVER] To: {self.user.username}, From: {event['sender']}, Content: {event.get('content', '')[:40]}")
            
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'content': event['content'],
            'sender': event['sender'],
            'sender_id': event['sender_id'],
            'avatar': event.get('avatar', ''),
            'timestamp': event['timestamp'],
            'message_id': event['message_id'],
            'id': event['id'],
            'is_media': event.get('is_media', False),
        }))
        print(f"✅ Delivered to {self.user.username}")

    async def media_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'media_message',
            'content': event['content'],
            'sender': event['sender'],
            'sender_id': event['sender_id'],
            'avatar': event.get('avatar', ''),
            'media_file': event['media_file'],
            'thumbnail_url': event.get('thumbnail_url'),
            'filename': event['filename'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id'],
            'id': event['id'],
            'is_media': True,
        }))

    async def typing_indicator(self, event):
        # Don't send typing indicator back to sender
        if event['sender'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'sender': event['sender'],
                'is_typing': event['is_typing'],
            }))

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'sender': event['sender'],
            'is_online': event['is_online'],
        }))

    @database_sync_to_async
    def save_message(self, room, sender, content, is_media, media_file=None, media_thumbnail=None):
        return Message.objects.create(
            room=room,
            sender=sender,
            content=content,
            is_media=is_media,
            media_file=media_file,
            media_thumbnail=media_thumbnail,
        )

    @database_sync_to_async
    def get_room(self, room_name):
        """Get or create room and ensure current user is a member"""
        room, created = Room.objects.get_or_create(name=room_name)
        
        if self.user.is_authenticated:
            # Add current user to room
            room.members.add(self.user)
            
            # For DM rooms with format "id1_id2", also ensure other user is added
            if '_' in room_name and not room.is_group:
                try:
                    ids = [int(x) for x in room_name.split('_')]
                    if len(ids) == 2:
                        # Get the other user ID
                        other_user_id = ids[0] if ids[1] == self.user.id else ids[1]
                        other_user = User.objects.get(id=other_user_id)
                        room.members.add(other_user)
                        print(f"✅ Ensured both users are in room: {self.user.username} and {other_user.username}")
                except (ValueError, User.DoesNotExist):
                    pass
        
        return room

    @database_sync_to_async
    def get_user_profile(self, user):
        try:
            return user.profile
        except:
            return UserProfile.objects.create(user=user)

    @database_sync_to_async
    def check_room_membership(self, room, user):
        """Check if user is a member of the room"""
        return room.members.filter(id=user.id).exists()

    @database_sync_to_async
    def is_room_member(self, room, user):
        """Check if user is a member - refresh from DB to ensure latest state"""
        room.refresh_from_db()
        return room.members.filter(id=user.id).exists()

    @database_sync_to_async
    def count_room_messages(self, room):
        """Count messages in a room"""
        return room.messages.count()

    @database_sync_to_async
    def set_user_online(self, is_online):
        if self.user.is_authenticated:
            try:
                profile = self.user.profile
            except:
                profile = UserProfile.objects.create(user=self.user)
            
            profile.is_online = is_online
            profile.save()

    @database_sync_to_async
    def save_file(self, file_bytes, filename, room):
        os.makedirs(f"{settings.MEDIA_ROOT}/messages/{room.name}", exist_ok=True)
        file_path = f"messages/{room.name}/{filename}"
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        
        with open(full_path, 'wb') as f:
            f.write(file_bytes)
        
        return file_path

    @database_sync_to_async
    def create_thumbnail(self, file_bytes, filename):
        try:
            img = Image.open(BytesIO(file_bytes))
            img.thumbnail((200, 200))
            
            thumbnail_filename = f"thumb_{filename}"
            os.makedirs(f"{settings.MEDIA_ROOT}/thumbnails", exist_ok=True)
            thumbnail_path = f"thumbnails/{thumbnail_filename}"
            full_path = os.path.join(settings.MEDIA_ROOT, thumbnail_path)
            
            img.save(full_path)
            return thumbnail_path
        except:
            return None
