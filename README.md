# Inderbara WhatsApp Clone
Production-Ready Real-Time Chat Application with End-to-End Encryption

## Features
✅ Django 5 + Channels 4 + Redis WebSockets  
✅ End-to-End RSA-OAEP (2048-bit) + AES-GCM Encryption  
✅ 100MB File Upload Limit  
✅ Real-Time Chat & Media Sharing  
✅ QR Code Mobile Linking  
✅ Dark WhatsApp-Like UI (Bootstrap 5 + Tailwind)  
✅ Multi-User WiFi LAN Access  
✅ Camera & Gallery Support  
✅ File Thumbnails & Previews  
✅ Mobile-First Responsive Design  

## System Requirements
- Python 3.11+
- Redis Server
- Windows/Linux/macOS

## Installation

### 1. Install Dependencies
```bash
cd inderbara_whatsapp_clone
pip install -r requirements.txt
```

### 2. Start Redis Server
**On Windows (using Windows Subsystem for Linux):**
```bash
redis-server
```

**Or use Docker:**
```bash
docker run -p 6379:6379 redis:latest
```

### 3. Run Django Migrations
```bash
python manage.py migrate
python manage.py makemigrations chat
python manage.py migrate chat
```

### 4. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 5. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 6. Start the Server
```bash
python manage.py runserver 0.0.0.0:8000
```

## Usage

### Desktop Access
1. Open your browser and navigate to `http://localhost:8000`
2. Click "Get Started" on the splash screen
3. A QR code will be generated

### Mobile Access (Same WiFi)
1. On mobile device, navigate to `http://<YOUR_LAPTOP_IP>:8000`
   - Replace `<YOUR_LAPTOP_IP>` with your computer's IP address (e.g., `192.168.1.100`)
2. Scan the QR code OR manually enter username
3. Start chatting!

### File Uploads
- Maximum file size: 100MB
- Supported formats: Images (.jpg, .png, .gif), Documents (.pdf, .doc, .docx), Archives (.zip)
- Drag & drop or click the attach button
- Camera uploads supported on mobile devices

### Admin Panel
- Access: `http://localhost:8000/admin`
- Login with your superuser credentials
- Manage rooms, messages, and user sessions

## Project Structure
```
inderbara_whatsapp_clone/
├── manage.py                 # Django management script
├── requirements.txt          # Dependencies
├── db.sqlite3               # Database (created after migration)
├── inderbara/               # Main project settings
│   ├── settings.py          # Django configuration
│   ├── asgi.py             # ASGI configuration for WebSockets
│   ├── urls.py             # URL routing
│   └── wsgi.py             # WSGI configuration
├── chat/                    # Chat app
│   ├── models.py           # Database models
│   ├── views.py            # Request handlers
│   ├── consumers.py        # WebSocket consumers
│   ├── routing.py          # WebSocket routing
│   ├── urls.py             # App URLs
│   ├── admin.py            # Admin configuration
│   └── migrations/         # Database migrations
├── templates/              # HTML templates
│   ├── base.html          # Base template
│   ├── splash.html        # Landing page
│   ├── login.html         # Device linking
│   └── chat.html          # Chat interface
├── static/                 # Static files
│   ├── css/
│   │   └── style.css      # Custom styling
│   ├── js/
│   │   └── app.js         # Frontend logic & encryption
│   └── images/
└── media/                  # User uploads
    ├── messages/
    ├── thumbnails/
    └── qr/

```

## Security Features

### End-to-End Encryption
- Client-side RSA-OAEP (2048-bit) key generation
- AES-GCM encryption for messages
- Messages encrypted before transmission
- Only encrypted data stored on server

### File Upload Security
- 100MB size limit (configurable)
- MIME type validation
- Automatic thumbnail generation with Pillow
- Encrypted file storage

### Session Management
- Unique session UUID per device
- Device name tracking
- IP address logging
- Auto-logout support

## Configuration

### Change File Upload Limit
Edit `inderbara/settings.py`:
```python
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB
```

### Change Redis Host
Edit `inderbara/settings.py`:
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],  # Change host/port here
        },
    },
}
```

### Enable HTTPS (Production)
```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## Troubleshooting

### Redis Connection Error
```
Error: Error -2 connecting to localhost:6379. Name or service not known.
```
**Solution:** Make sure Redis server is running.

### Port Already in Use
```
Error: Address already in use
```
**Solution:** Use a different port: `python manage.py runserver 0.0.0.0:8001`

### WebSocket Connection Failed
**Solution:** Ensure Daphne is properly configured in ASGI

### Static Files Not Loading
```bash
python manage.py collectstatic --noinput --clear
```

## Performance Optimization

1. **Enable Compression:**
   - Add `whitenoise.middleware.WhiteNoiseMiddleware` for static files

2. **Database Optimization:**
   - Add indexes to frequently queried fields
   - Use select_related() and prefetch_related()

3. **Redis Optimization:**
   - Configure persistence (RDB/AOF)
   - Set appropriate memory limits

## Production Deployment

### Using Gunicorn + Nginx
```bash
pip install gunicorn
gunicorn inderbara.wsgi --bind 0.0.0.0:8000
```

### Using Docker
Create a `Dockerfile` and `docker-compose.yml`

### Environment Variables
Create `.env` file:
```
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
REDIS_HOST=redis
REDIS_PORT=6379
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Splash screen |
| `/qr-login/` | GET | Generate QR code |
| `/link/<uuid>/` | GET, POST | Device linking |
| `/chat/` | GET | Chat interface |
| `/download/<uuid>/` | GET | Download message file |
| `/admin/` | GET | Admin panel |
| `/ws/chat/<room>/` | WS | WebSocket connection |

## WebSocket Events

### Client → Server
- `chat_message`: Send text message
- `media_message`: Send file/image
- `typing`: Typing indicator

### Server → Client
- `chat_message`: Receive text message
- `media_message`: Receive file/image
- `typing_indicator`: Show typing status

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Django | 5.0.7 | Web framework |
| channels | 4.1.0 | WebSocket support |
| channels-redis | 4.2.0 | Redis backend |
| daphne | 4.1.0 | ASGI server |
| redis | 5.0.1 | Redis client |
| Pillow | 10.4.0 | Image processing |
| qrcode | 7.4.2 | QR code generation |
| cryptography | 46.0.5 | Cryptography library |

## Current Limitations

1. No audio/video calling (can be added with Jitsi/TWILIO)
2. No message search (can add Elasticsearch)
3. No message reactions (can add emoji reactions)
4. No read receipts (can implement with DB flags)
5. SQLite for dev (use PostgreSQL for production)

## Future Enhancements

- ✨ Voice/video calling (WebRTC)
- ✨ Message reactions & emoji support
- ✨ Status updates
- ✨ Backup & restore
- ✨ Message search
- ✨ Activity tracking
- ✨ User profiles
- ✨ Group administration controls

## License
MIT License - Open Source

## Support
For issues and questions, please check the troubleshooting section above.

## Author
Inderbara Development Team

---

**Ready to deploy!** Start the server and enjoy your secure chat application.
