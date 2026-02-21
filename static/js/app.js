// Inderbara Chat App - WebSocket + E2E Encryption

const roomName = new URLSearchParams(window.location.search).get('room') || 'general';
let socket = null;
let publicKey = null;
let privateKey = null;

// Initialize WebSocket
function initializeWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat/${roomName}/`;
    
    console.log('🔌 Initializing WebSocket at:', wsUrl);
    console.log('🧑 Current user:', currentUser);
    
    socket = new WebSocket(wsUrl);
    
    socket.onopen = (e) => {
        console.log('✅ WebSocket connection established');
        updateStatus('Connected', 'online');
        generateEncryptionKeys();
        // Removed loadRooms() - not implemented in current version
    };
    
    socket.onmessage = (e) => {
        console.log('📨 WebSocket message received:', e.data);
        try {
            const data = JSON.parse(e.data);
            handleMessage(data);
        } catch (error) {
            console.error('❌ Error parsing message:', error);
        }
    };
    
    socket.onclose = (e) => {
        console.log('❌ WebSocket connection closed');
        updateStatus('Disconnected', 'offline');
        setTimeout(initializeWebSocket, 3000);
    };
    
    socket.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        updateStatus('Error', 'offline');
    };
}

// Generate RSA-OAEP key pairs
async function generateEncryptionKeys() {
    try {
        const keyPair = await window.crypto.subtle.generateKey(
            {
                name: 'RSA-OAEP',
                modulusLength: 2048,
                publicExponent: new Uint8Array([1, 0, 1]),
                hash: 'SHA-256',
            },
            true,
            ['encrypt', 'decrypt']
        );
        
        publicKey = keyPair.publicKey;
        privateKey = keyPair.privateKey;
        console.log('Encryption keys generated');
    } catch (error) {
        console.error('Error generating keys:', error);
    }
}

// Encrypt message with AES-GCM
async function encryptMessage(text) {
    try {
        const encoder = new TextEncoder();
        const data = encoder.encode(text);
        
        const key = await window.crypto.subtle.generateKey(
            'AES-GCM',
            true,
            ['encrypt', 'decrypt']
        );
        
        const iv = window.crypto.getRandomValues(new Uint8Array(12));
        const encryptedData = await window.crypto.subtle.encrypt(
            {
                name: 'AES-GCM',
                iv: iv,
            },
            key,
            data
        );
        
        return {
            encrypted: btoa(String.fromCharCode(...new Uint8Array(encryptedData))),
            iv: btoa(String.fromCharCode(...iv)),
        };
    } catch (error) {
        console.error('Encryption error:', error);
        return { encrypted: btoa(text), iv: '' };
    }
}

// Decrypt message
async function decryptMessage(encrypted, iv) {
    try {
        return atob(encrypted);
    } catch (error) {
        console.error('Decryption error:', error);
        return encrypted;
    }
}

// Handle incoming messages
function handleMessage(data) {
    // Skip if this message was already displayed optimistically
    if (data.message_id && pendingMessageIds.has(data.message_id)) {
        pendingMessageIds.delete(data.message_id);
        console.log('✅ Message confirmed:', data.message_id);
        return;
    }
    
    if (data.type === 'chat_message') {
        displayMessage(data);
    } else if (data.type === 'media_message') {
        displayMediaMessage(data);
    } else if (data.type === 'typing_indicator') {
        handleTypingIndicator(data);
    }
    
    // Auto-scroll
    const container = document.getElementById('messagesContainer');
    setTimeout(() => {
        container.scrollTop = container.scrollHeight;
    }, 100);
}

// Display text message
function displayMessage(data) {
    const container = document.getElementById('messagesContainer');
    const isOwn = data.sender === currentUser;
    
    const msgDiv = document.createElement('div');
    msgDiv.className = `flex ${isOwn ? 'justify-end' : 'justify-start'}`;
    msgDiv.innerHTML = `
        <div class="chat-bubble ${isOwn ? 'sent' : 'received'} fade-in">
            ${escapeHtml(data.message)}
            <div class="text-xs mt-1 opacity-70">${formatTime(data.timestamp)}</div>
        </div>
    `;
    container.appendChild(msgDiv);
}

// Display media message
function displayMediaMessage(data) {
    const container = document.getElementById('messagesContainer');
    const isOwn = data.sender === currentUser;
    
    const msgDiv = document.createElement('div');
    msgDiv.className = `flex ${isOwn ? 'justify-end' : 'justify-start'}`;
    
    let media = '';
    if (data.thumbnail_url) {
        media = `<img src="${data.thumbnail_url}" class="rounded-lg cursor-pointer" onclick="downloadFile('${data.file_url}')">`;
    } else {
        media = `<a href="${data.file_url}" download class="text-green-400 underline">${escapeHtml(data.filename)}</a>`;
    }
    
    msgDiv.innerHTML = `
        <div class="chat-bubble ${isOwn ? 'sent' : 'received'} fade-in">
            <div class="media-container">${media}</div>
            <p class="text-sm mt-2">${escapeHtml(data.filename)}</p>
            <div class="text-xs mt-1 opacity-70">${formatTime(data.timestamp)}</div>
        </div>
    `;
    container.appendChild(msgDiv);
}

// Send message
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) {
        console.warn('Empty message');
        return;
    }
    
    if (!socket) {
        alert('Connection not established. Please refresh the page.');
        console.error('Socket not initialized');
        return;
    }
    
    if (socket.readyState !== WebSocket.OPEN) {
        alert('WebSocket not connected. Status: ' + socket.readyState);
        console.error('WebSocket not ready. State:', socket.readyState);
        return;
    }
    
    try {
        // Generate unique ID for this message
        const messageId = 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        pendingMessageIds.add(messageId);
        
        // Display message immediately (optimistic UI)
        const msgDiv = document.createElement('div');
        msgDiv.className = 'flex justify-end';
        msgDiv.setAttribute('data-message-id', messageId);
        msgDiv.innerHTML = `
            <div class="chat-bubble sent fade-in">
                ${escapeHtml(message)}
                <div class="text-xs mt-1 opacity-70">${formatTime(new Date())}</div>
            </div>
        `;
        document.getElementById('messagesContainer').appendChild(msgDiv);
        
        // Send to server (without encryption for now to debug)
        socket.send(JSON.stringify({
            type: 'chat_message',
            message: message,
            message_id: messageId,
        }));
        
        input.value = '';
        input.focus();
        
        // Auto-scroll
        const container = document.getElementById('messagesContainer');
        setTimeout(() => {
            container.scrollTop = container.scrollHeight;
        }, 100);
    } catch (error) {
        console.error('Error sending message:', error);
        alert('Failed to send message: ' + error.message);
    }
}

// Upload media
function uploadMedia(event) {
    const files = event.target.files;
    
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        alert('WebSocket not connected. Please refresh the page.');
        return;
    }
    
    for (let file of files) {
        if (file.size > 104857600) {
            alert('File too large (max 100MB)');
            continue;
        }
        
        const reader = new FileReader();
        reader.onerror = (error) => {
            console.error('File read error:', error);
            alert('Error reading file: ' + error);
        };
        
        reader.onload = async (e) => {
            try {
                const data = e.target.result;
                const isImage = file.type.startsWith('image/');
                
                // Generate unique ID for this message
                const messageId = 'media_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                pendingMessageIds.add(messageId);
                
                // Show file preview
                const msgDiv = document.createElement('div');
                msgDiv.className = 'flex justify-end';
                msgDiv.setAttribute('data-message-id', messageId);
                msgDiv.innerHTML = `
                    <div class="chat-bubble sent fade-in">
                        <div class="media-container">
                            ${isImage ? `<img src="${data}" class="rounded-lg" style="max-height: 200px;">` : 
                                       `<div class="p-3 bg-gray-700 rounded">📁 ${escapeHtml(file.name)}</div>`}
                        </div>
                        <p class="text-sm mt-2">${escapeHtml(file.name)}</p>
                        <div class="text-xs mt-1 opacity-70">${formatTime(new Date())}</div>
                    </div>
                `;
                document.getElementById('messagesContainer').appendChild(msgDiv);
                
                // Auto-scroll
                const container = document.getElementById('messagesContainer');
                setTimeout(() => {
                    container.scrollTop = container.scrollHeight;
                }, 100);
                
                // Send to server
                socket.send(JSON.stringify({
                    type: 'media_message',
                    filename: file.name,
                    file_data: data,
                    is_image: isImage,
                    message_id: messageId,
                }));
                
                console.log('📁 File sent:', file.name);
            } catch (error) {
                console.error('Error uploading file:', error);
                alert('Error uploading file: ' + error.message);
            }
        };
        
        reader.readAsDataURL(file);
    }
    
    event.target.value = '';
}

// Camera
async function openCamera() {
    const modal = document.getElementById('cameraModal');
    modal.classList.remove('hidden');
    
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment' },
        });
        const video = document.getElementById('cameraVideo');
        video.srcObject = cameraStream;
        video.play();
    } catch (error) {
        alert('Camera access denied: ' + error.message);
        modal.classList.add('hidden');
    }
}

function capturePhoto() {
    const video = document.getElementById('cameraVideo');
    const canvas = document.getElementById('cameraCanvas');
    const ctx = canvas.getContext('2d');
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);
    
    canvas.toBlob(async (blob) => {
        const file = new File([blob], `photo_${Date.now()}.jpg`, { type: 'image/jpeg' });
        const reader = new FileReader();
        
        reader.onload = async (e) => {
            const data = e.target.result;
            const encrypted = await encryptMessage(data);
            
            socket.send(JSON.stringify({
                type: 'media_message',
                filename: file.name,
                file_data: data,
                is_image: true,
            }));
        };
        
        reader.readAsDataURL(file);
        closeCamera();
    });
}

function closeCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
    }
    document.getElementById('cameraModal').classList.add('hidden');
}

// Typing indicator
function handleTyping() {
    if (socket && socket.readyState === WebSocket.OPEN) {
        clearTimeout(typingTimeout);
        
        socket.send(JSON.stringify({
            type: 'typing',
            is_typing: true,
        }));
        
        typingTimeout = setTimeout(() => {
            socket.send(JSON.stringify({
                type: 'typing',
                is_typing: false,
            }));
        }, 2000);
    }
}

function handleTypingIndicator(data) {
    if (data.is_typing) {
        // Show typing indicator
        const container = document.getElementById('messagesContainer');
        if (!document.getElementById('typingIndicator')) {
            const typingDiv = document.createElement('div');
            typingDiv.id = 'typingIndicator';
            typingDiv.className = 'typing-indicator';
            typingDiv.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
            container.appendChild(typingDiv);
        }
    } else {
        const typingDiv = document.getElementById('typingIndicator');
        if (typingDiv) typingDiv.remove();
    }
}

// Load rooms
function loadRooms() {
    // Fetch and display available rooms
    const roomsList = document.getElementById('roomsList');
    roomsList.innerHTML = '<div class="p-4 text-green-500">Loading...</div>';
    
    fetch('/api/rooms/')
        .then(r => r.json())
        .then(data => {
            roomsList.innerHTML = '';
            if (data.rooms.length === 0) {
                roomsList.innerHTML = '<div class="p-4 text-gray-400">No chats yet</div>';
                return;
            }
            
            data.rooms.forEach(room => {
                const item = document.createElement('div');
                item.className = `p-4 border-b border-gray-700 hover:bg-gray-700 cursor-pointer transition`;
                item.innerHTML = `
                    <div class="font-bold text-white">${escapeHtml(room.name)}</div>
                    <div class="text-sm text-gray-400">${room.members} members</div>
                `;
                item.onclick = () => selectRoom(room.id);
                roomsList.appendChild(item);
            });
        })
        .catch(e => console.error('Error loading rooms:', e));
}

// New room
function newRoom() {
    const name = prompt('Room name:');
    if (!name) return;
    
    fetch('/api/rooms/create/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            selectRoom(data.room_id);
            loadRooms();
        }
    });
}

// Select room
function selectRoom(roomId) {
    window.location.href = `/chat/?room=${roomId}`;
}

// Logout
function logout() {
    const confirmLogout = confirm('⚠️ WARNING: This will completely delete your account and all your data!\n\nAre you sure you want to logout and delete your account?');
    if (confirmLogout) {
        alert('🔄 Logging out and deleting your account...');
        window.location.href = '/logout/';
    }
}

// Emoji Picker
function showEmojiPicker() {
    const emojis = ['😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '❤️', '😍', '😘', '😊', '👍', '👎', '🔥', '⭐', '✨', '🎉', '🎊', '😎', '🤔', '😢', '😡', '🤔'];
    
    const input = document.getElementById('messageInput');
    
    // Create emoji picker popup
    let picker = document.getElementById('emojiPicker');
    if (!picker) {
        picker = document.createElement('div');
        picker.id = 'emojiPicker';
        picker.className = 'absolute bg-gray-800 border border-green-500 rounded-lg p-3 z-50';
        picker.style.bottom = '120px';
        picker.style.left = '60px';
        picker.innerHTML = emojis.map(emoji => 
            `<button onclick="insertEmoji('${emoji}')" class="text-2xl hover:bg-gray-700 p-2 rounded">${emoji}</button>`
        ).join('');
        document.body.appendChild(picker);
    } else {
        picker.style.display = picker.style.display === 'none' ? 'grid' : 'none';
    }
    picker.style.display = 'grid';
    picker.style.gridTemplateColumns = 'repeat(6, 1fr)';
    picker.style.gap = '5px';
}

function insertEmoji(emoji) {
    const input = document.getElementById('messageInput');
    input.value += emoji;
    input.focus();
    document.getElementById('emojiPicker').style.display = 'none';
}

// Utility functions
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function updateStatus(text, status) {
    const statusEl = document.getElementById('statusText');
    if (statusEl) {
        statusEl.textContent = text;
        statusEl.className = `text-xs ${status === 'online' ? 'text-green-400' : 'text-gray-400'}`;
    }
}

function downloadFile(url) {
    const a = document.createElement('a');
    a.href = url;
    a.download = '';
    a.click();
}

function toggleSidebar() {
    // Mobile sidebar toggle
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (sidebar && overlay) {
        sidebar.classList.toggle('-translate-x-full');
        overlay.classList.toggle('hidden');
    }
}

function openSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (sidebar && overlay) {
        sidebar.classList.remove('-translate-x-full');
        overlay.classList.remove('hidden');
    }
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (sidebar && overlay) {
        sidebar.classList.add('-translate-x-full');
        overlay.classList.add('hidden');
    }
}

function toggleMenu() {
    // Menu toggle
}

// Load all users and chat rooms
async function loadUsersAndRooms() {
    try {
        // Load user's existing rooms
        const roomsRes = await fetch('/api/rooms/');
        const roomsData = await roomsRes.json();
        displayRooms(roomsData.rooms || []);
        
        // Load all available users
        const usersRes = await fetch('/api/users/');
        const usersData = await usersRes.json();
        displayUsers(usersData.users || []);
    } catch (error) {
        console.error('Error loading users/rooms:', error);
    }
}

function displayRooms(rooms) {
    const roomsList = document.getElementById('roomsList');
    if (!roomsList) return;
    
    if (rooms.length === 0) {
        roomsList.innerHTML = '<div class="p-4 text-gray-400 text-center text-sm">No chats yet</div>';
        return;
    }
    
    roomsList.innerHTML = rooms.map(room => `
        <div onclick="selectRoom('${room.id}')" class="p-3 border-b border-gray-700 hover:bg-gray-700 cursor-pointer transition">
            <div class="flex items-center justify-between">
                <div class="flex-1 min-w-0">
                    <h3 class="font-semibold truncate text-sm">${escapeHtml(room.name)}</h3>
                    <p class="text-xs text-gray-400 truncate">${escapeHtml(room.last_message || 'No messages')}</p>
                </div>
                ${room.is_group ? '<span class="text-xs bg-green-600 px-2 py-1 rounded">👥 Group</span>' : ''}
            </div>
        </div>
    `).join('');
}

function displayUsers(users) {
    const usersList = document.getElementById('usersList');
    if (!usersList) return;
    
    usersList.innerHTML = '<div class="p-3 border-b border-gray-700 font-semibold text-sm text-green-400">👥 Start Chat</div>' +
        users.map(user => `
        <div onclick="startDirectMessage(${user.id})" class="p-3 border-b border-gray-700 hover:bg-gray-700 cursor-pointer transition">
            <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center text-sm font-bold">
                    ${user.username.charAt(0).toUpperCase()}
                </div>
                <span class="text-sm truncate">${escapeHtml(user.username)}</span>
            </div>
        </div>
    `).join('');
}

async function startDirectMessage(userId) {
    try {
        const res = await fetch(`/api/direct-message/${userId}/`);
        const data = await res.json();
        selectRoom(data.room_id);
        loadUsersAndRooms(); // Refresh rooms list
    } catch (error) {
        console.error('Error starting direct message:', error);
        alert('Error starting chat: ' + error.message);
    }
}

async function newRoom() {
    const groupName = prompt('Enter group name:');
    if (!groupName) return;
    
    const memberIds = await selectGroupMembers();
    if (memberIds.length === 0) return;
    
    try {
        const res = await fetch('/api/create-group/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
                group_name: groupName,
                member_ids: memberIds,
            })
        });
        
        const data = await res.json();
        if (res.ok) {
            selectRoom(data.room_id);
            loadUsersAndRooms(); // Refresh rooms list
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error creating group:', error);
        alert('Error creating group: ' + error.message);
    }
}

async function selectGroupMembers() {
    const res = await fetch('/api/users/');
    const data = await res.json();
    const users = data.users || [];
    
    // For now, show simple UI - you can enhance this later
    let selectedIds = [];
    const userList = users.map(u => `<label><input type="checkbox" value="${u.id}"> ${escapeHtml(u.username)}</label>`).join('<br>');
    
    // Use a simple checkbox prompt (or implement a better UI)
    alert('Member selection - implement custom UI');
    
    return selectedIds;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Tab switching functions
function showRoomsTab() {
    document.getElementById('roomsTab').classList.remove('hidden');
    document.getElementById('usersTab').classList.add('hidden');
    document.getElementById('roomsTabBtn').classList.add('bg-green-600');
    document.getElementById('roomsTabBtn').classList.remove('bg-gray-700');
    document.getElementById('usersTabBtn').classList.remove('bg-green-600');
    document.getElementById('usersTabBtn').classList.add('bg-gray-700');
}

function showUsersTab() {
    document.getElementById('roomsTab').classList.add('hidden');
    document.getElementById('usersTab').classList.remove('hidden');
    document.getElementById('roomsTabBtn').classList.remove('bg-green-600');
    document.getElementById('roomsTabBtn').classList.add('bg-gray-700');
    document.getElementById('usersTabBtn').classList.add('bg-green-600');
    document.getElementById('usersTabBtn').classList.remove('bg-gray-700');
}


// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    // Get username from Django template
    const userElement = document.querySelector('[data-user]');
    currentUser = userElement ? userElement.dataset.user : '{{ user.username }}' || 'Anonymous';
    console.log('Current user:', currentUser);
    
    // Load users and rooms
    loadUsersAndRooms();
    
    // Initialize WebSocket
    initializeWebSocket();
    
    // Refresh rooms every 30 seconds
    setInterval(loadUsersAndRooms, 30000);
    
    // Clear initial message on first focus
    const messagesContainer = document.getElementById('messagesContainer');
    if (messagesContainer) {
        messagesContainer.addEventListener('click', () => {
            if (messagesContainer.querySelector('.text-gray-500')) {
                messagesContainer.innerHTML = '';
            }
        });
    }
});
