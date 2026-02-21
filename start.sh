#!/bin/bash
# Inderbara WhatsApp Clone - Linux/macOS Startup Script

echo "========================================"
echo "   Inderbara - WhatsApp Clone"
echo "   Starting Server..."
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    exit 1
fi

# Check if Redis is running (optional warning)
if ! command -v redis-cli &> /dev/null; then
    echo "Warning: Redis is not installed or not in PATH."
    echo "Make sure Redis server is running in a separate terminal."
    echo
fi

# Run Django development server
echo "Starting Django server on http://localhost:8000"
python3 manage.py runserver 0.0.0.0:8000
