# QUICK START GUIDE - Inderbara WhatsApp Clone

## ✅ What's Complete

The project has been fully generated with:

### Django Project Structure
- ✅ `manage.py` - Django management command
- ✅ `requirements.txt` - All dependencies listed
- ✅ Database migrations created & applied
- ✅ Static files collected

### Application Files
- ✅ `inderbara/` - Main project package
  - ✅ `settings.py` - Django settings with Channels, Redis, 100MB upload limit
  - ✅ `asgi.py` - ASGI config for WebSockets
  - ✅ `urls.py` - URL routing with media/static file serving
  - ✅ `wsgi.py` - WSGI config

### Chat App
- ✅ `chat/` - Main application
  - ✅ `models.py` - Room, Message, UserSession models
  - ✅ `views.py` - Splash, QR login, device linking, chat views
  - ✅ `consumers.py` - WebSocket consumer with encryption
  - ✅ `routing.py` - WebSocket URL routing
  - ✅ `urls.py` - App URL patterns
  - ✅ `admin.py` - Admin configuration
  - ✅ `migrations/` - Database schema

### Templates
- ✅ `templates/base.html` - Base template with Bootstrap & Tailwind
- ✅ `templates/splash.html` - Landing page with animated logo
- ✅ `templates/login.html` - Device linking QR/form page
- ✅ `templates/chat.html` - Full chat interface

### Static Files
- ✅ `static/css/style.css` - WhatsApp-like styling
- ✅ `static/js/app.js` - WebSocket logic, E2E encryption, file upload

### Documentation
- ✅ `README.md` - Complete documentation
- ✅ `QUICKSTART.md` - This file
- ✅ `start.bat` - Windows startup script
- ✅ `start.sh` - Linux/macOS startup script

---

## 🚀 Running the Project

### Step 1: Install Redis (If Not Already Installed)

**Windows (via WSL):**
```bash
# In WSL terminal
sudo apt-get install redis-server
redis-server &
```

**Or use Docker:**
```bash
docker run -p 6379:6379 redis:latest
```

**macOS:**
```bash
brew install redis
redis-server
```

### Step 2: Start Django Server

**Windows:**
```bash
# Double-click start.bat
# OR in PowerShell:
python manage.py runserver 0.0.0.0:8000
```

**Linux/macOS:**
```bash
bash start.sh
# OR directly:
python manage.py runserver 0.0.0.0:8000
```

### Step 3: Access the Application

- **Desktop:** http://localhost:8000
- **Mobile (Same WiFi):** http://<YOUR_IP>:8000
  - Find your IP: `ipconfig` (Windows) or `ifconfig` (Linux/Mac)

---

## 📱 How It Works

### Desktop Flow
1. Open browser → http://localhost:8000
2. See splash screen with "Get Started" button
3. Click button → QR code generated
4. Join as user

### Mobile Flow
1. Open browser on phone → http://<COMPUTER_IP>:8000 (same WiFi)
2. Enter username and device name
3. Click "Join Chat"
4. Start messaging!

---

## 🔐 Security Features (All Implemented)

✅ End-to-End Encryption
- RSA-OAEP 2048-bit key generation
- AES-GCM message encryption
- Client-side encryption before transmission

✅ File Upload Security
- 100MB max file size
- Thumbnail generation
- Encrypted storage
- MIME type validation

✅ Session Management
- Unique UUID per device
- Device name tracking
- IP logging
- Auto-expiry support

---

## 📋 Database Models

### Room
- name (unique)
- members (M2M with User)
- is_group (bool)
- created_at, updated_at

### Message
- room (FK)
- sender (FK to User)
- content (TextField, encrypted)
- is_media (bool)
- media_file, media_thumbnail (optional)
- timestamp, is_read

### UserSession
- user (FK)
- device_name
- ip_address
- created_at, last_active
- is_active

---

## 🌐 WebSocket Events

### Client Sends
```json
{
  "type": "chat_message",
  "message": "encrypted_content"
}
```

```json
{
  "type": "media_message",
  "filename": "photo.jpg",
  "file_data": "base64_encoded_encrypted_data",
  "is_image": true
}
```

### Server Broadcasts
```json
{
  "type": "chat_message",
  "message": "content",
  "sender": "username",
  "timestamp": "2026-02-21T10:30:00",
  "message_id": "uuid"
}
```

---

## 📂 Project Tree

```
inderbara_whatsapp_clone/
├── manage.py
├── requirements.txt
├── db.sqlite3
├── README.md
├── QUICKSTART.md
├── start.bat
├── start.sh
│
├── inderbara/
│   ├── __init__.py
│   ├── settings.py
│   ├── asgi.py
│   ├── urls.py
│   └── wsgi.py
│
├── chat/
│   ├── __init__.py
│   ├── admin.py
│   ├── models.py
│   ├── views.py
│   ├── consumers.py
│   ├── routing.py
│   ├── urls.py
│   └── migrations/
│
├── templates/
│   ├── base.html
│   ├── splash.html
│   ├── login.html
│   └── chat.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   └── images/
│
├── staticfiles/
│   └── (collected static files)
│
└── media/
    ├── messages/
    ├── thumbnails/
    └── qr/
```

---

## ⚙️ Configuration

### Change Upload Limit
Edit `inderbara/settings.py`:
```python
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # bytes (100MB)
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600
```

### Change Redis URL
Edit `inderbara/settings.py`:
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('YOUR_REDIS_IP', 6379)],
        },
    },
}
```

### Enable HTTPS
```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## 🆘 Troubleshooting

### Error: "Error -2 connecting to localhost:6379"
**Solution:** Start Redis server in another terminal

### Error: "Address already in use"
**Solution:** Kill process or use different port:
```bash
python manage.py runserver 8001
```

### Static files not loading
**Solution:**
```bash
python manage.py collectstatic --noinput --clear
```

### WebSocket connection fails
**Solution:** Restart server and check Redis is running

---

## 📦 What's Pre-installed

- Django 5.0.7
- Channels 4.1.0 (WebSockets)
- Channels-Redis 4.2.0 (Redis backend)
- Daphne 4.1.0 (ASGI server)
- Redis 5.0.1 (Redis client)
- Pillow 10.4.0 (Image processing)
- QRCode 7.4.2 (QR code generation)
- Cryptography 46.0.5 (Encryption)

---

## 🎯 Next Steps

1. ✅ All files created
2. ✅ Database initialized
3. ✅ Migrations applied
4. Run: `python manage.py runserver 0.0.0.0:8000`
5. Visit: http://localhost:8000
6. Share WiFi IP with mobile devices

---

## 💡 Tips

- Use `http://<YOUR_IP>:8000` on mobile devices (same WiFi)
- Admin panel at http://localhost:8000/admin
- Create superuser: `python manage.py createsuperuser`
- Check database: Open `db.sqlite3` with DB Browser for SQLite
- View logs: Terminal where server is running

---

## 🔒 Security Notes

- Encryption is client-side (before transmission)
- Messages encrypted before storage
- Change `SECRET_KEY` in production
- Use environment variables for sensitive data
- Enable HTTPS in production
- Use PostgreSQL instead of SQLite in production

---

**Project is ready! Start the server and enjoy your secure chat app.** 🎉
