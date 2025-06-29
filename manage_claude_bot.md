# Claude Terminal Bot Management Script Usage

This document describes how to use the `manage_claude_bot.sh` script to control your voice-controlled terminal bot and manage sessions.

## 🚀 Basic Commands

```bash
# Start the Claude Bot
./manage_claude_bot.sh start

# Stop the Claude Bot  
./manage_claude_bot.sh stop

# Restart the Claude Bot
./manage_claude_bot.sh restart

# Check if the bot is running
./manage_claude_bot.sh status

# Get help
./manage_claude_bot.sh help
```

## 📊 Monitoring & Debugging

```bash
# Show last 50 lines of logs
./manage_claude_bot.sh logs

# Show last 100 lines of logs
./manage_claude_bot.sh logs 100

# Follow logs in real-time (like tail -f)
./manage_claude_bot.sh tail

# Test bot setup and dependencies
./manage_claude_bot.sh test
```

## 📱 Session Management

```bash
# List all active sessions
./manage_claude_bot.sh sessions list

# Clean up orphaned tmux sessions
./manage_claude_bot.sh sessions clean
```

## 🌐 Web Interface

```bash
# Start the web interface (http://localhost:8080)
./manage_claude_bot.sh web
```

## 🎤 Voice Commands (via Zulip)

Once the bot is running, you can send these commands via Zulip (voice-to-text or typing):

### Session Management
- `/new-session "odoo-development"` - Create a new terminal session
- `/list-sessions` - Show all active sessions  
- `/switch-session 002` - Switch to session 002
- `/sleep-session 002` - Background session 002
- `/kill-session 002` - Terminate session 002

### Claude Code Integration
- `/claude-start` - Initialize Claude Code in current session
- `/claude-stop` - Stop Claude Code
- `/claude-status` - Check Claude Code status

### Context & Files
- `/context upload filename.py` - Upload file to session context
- `/context list` - Show session context files
- `/working-dir /path/to/project` - Change session working directory

### Terminal Commands
Send any non-slash message to execute as a terminal command:
- `pwd` - Show current directory
- `ls -la` - List files
- `git status` - Git commands
- `python manage.py runserver` - Run development servers

## 🛠️ Troubleshooting

### Bot Won't Start
```bash
# Test the setup
./manage_claude_bot.sh test

# Check for API key configuration
grep "YOUR_API_KEY_HERE" config.yaml
# If found, update config.yaml with your Zulip bot API key
```

### Multiple Responses
```bash
# Check for multiple bot processes
ps aux | grep claude_bot

# Clean restart
./manage_claude_bot.sh stop
./manage_claude_bot.sh start
```

### Session Issues
```bash
# Clean up orphaned tmux sessions
./manage_claude_bot.sh sessions clean

# List active sessions
./manage_claude_bot.sh sessions list
```

### Log Analysis
```bash
# Follow logs in real-time
./manage_claude_bot.sh tail

# Check recent errors
./manage_claude_bot.sh logs 100 | grep ERROR
```

## 📋 Development Workflow

### Starting Your Day
```bash
# Start the bot
./manage_claude_bot.sh start

# Check status
./manage_claude_bot.sh status

# Monitor activity
./manage_claude_bot.sh tail
```

### Voice Development Session
1. **Send voice message**: "New session Odoo payment module"
2. **Switch project**: "Working directory /Users/dgoo2308/git/odoo18"
3. **Start Claude**: "Start Claude Code"
4. **Develop**: "Analyze the payment models structure"
5. **Test**: "Run the test suite"

### Ending Your Day
```bash
# Stop the bot
./manage_claude_bot.sh stop

# Or just leave it running for remote access
```

## 🔧 Configuration

The script automatically handles:
- ✅ Virtual environment activation
- ✅ PID file management
- ✅ Log rotation and monitoring
- ✅ Process cleanup
- ✅ Dependency checking
- ✅ API key validation

## 📱 Mobile Integration

Perfect for iPhone voice-to-text workflow:
1. **Open Zulip mobile app**
2. **Use voice-to-text**: Natural speech commands
3. **Bot processes**: Commands execute on your Mac
4. **Results**: Delivered back to Zulip instantly

## 🎯 Advanced Usage

### Custom Project Sessions
```bash
# Via voice: "New session Odoo eighteen inventory module"
# Then: "Working directory git Odoo eighteen"
# Then: "Start Claude Code"
```

### Remote Development
- Bot runs locally on your Mac
- Access via Zulip from anywhere
- All secrets stay on your laptop
- Perfect for coffee shop coding!

---

**Your voice-controlled development environment is now fully managed!** 🎤→📱→🤖→💻
