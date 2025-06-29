#!/bin/bash
# Web Interface Launcher Script

cd /Users/dgoo2308/git/claude-bot

# Activate virtual environment
source venv/bin/activate

# Start the web interface
echo "🌐 Starting Claude Bot Web Interface..."
echo "Visit http://localhost:8080 in your browser"
python web_interface.py
