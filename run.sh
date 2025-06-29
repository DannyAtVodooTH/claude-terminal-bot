#!/bin/bash
# Claude Bot Launcher Script

cd /Users/dgoo2308/git/claude-bot

# Activate virtual environment
source venv/bin/activate

# Check if config has API key
if grep -q "YOUR_API_KEY_HERE" config.yaml; then
    echo "⚠️  Please update config.yaml with your Zulip API key first!"
    echo "Visit https://v-odoo.zulipchat.com to create a bot and get API key"
    exit 1
fi

# Start the bot
echo "🤖 Starting Claude Terminal Bot..."
python claude_bot.py
