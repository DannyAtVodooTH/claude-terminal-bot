# 🎤 Claude Terminal Bot

> **Revolutionary Voice-Controlled AI Development Environment**

Transform your iPhone into a powerful terminal controller. Code, debug, and manage development sessions using natural voice commands powered by AI.

## 🚀 Features

- **🎤 Voice-to-Text Development**: Control terminal sessions from your iPhone via Zulip
- **🤖 Claude Code Integration**: AI-assisted programming with voice commands  
- **📱 Mobile-First Design**: Perfect for coffee shop coding and remote development
- **🔒 Security by Design**: All secrets stay on your laptop, zero cloud dependencies
- **⚡ Session Management**: Persistent tmux sessions with context preservation
- **🧠 Natural Language**: "Start Claude code" automatically becomes `/claude-start`

## 🎯 Quick Demo

```
Voice: "New session Odoo payment module"     → Creates development session
Voice: "Start Claude code"                   → Launches AI assistant  
Voice: "Analyze the payment models"          → AI reviews your code
Voice: "Git status"                          → Shows repository status
Voice: "Switch to session two"               → Changes active session
```

## 📱 Perfect For

- **☕ Coffee Shop Development**: Code from anywhere with just your phone
- **♿ Accessibility**: Hands-free development for enhanced accessibility
- **🏠 Remote Work**: Access your development environment from any location
- **🤝 Pair Programming**: Voice-controlled AI assistance
- **🚗 Mobile Debugging**: Quick fixes and status checks on the go

## 🛠️ Installation

### Prerequisites
- **macOS** with Python 3.9+
- **tmux**: `brew install tmux`
- **Zulip account** (free at zulip.com)
- **iPhone** with Zulip mobile app

### Quick Start
```bash
# Clone the repository
git clone https://github.com/v-odoo/claude-terminal-bot.git
cd claude-terminal-bot

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure your Zulip bot
cp config.example.yaml config.yaml
# Edit config.yaml with your Zulip credentials

# Start the bot
./manage_claude_bot.sh start
```

### Zulip Bot Setup
1. Go to your Zulip instance → Settings → Your bots
2. Create a new "Generic bot" 
3. Copy the API key to `config.yaml`
4. Subscribe the bot to your desired stream

## 🎤 Voice Commands

### Session Management
- `"New session project-name"` → Create terminal session
- `"List sessions"` → Show active sessions
- `"Switch to session 002"` → Change active session
- `"Working directory /path/to/project"` → Change project directory

### AI Development
- `"Start Claude code"` → Launch AI assistant
- `"Analyze this code"` → AI code review
- `"Help me debug this error"` → AI debugging assistance
- `"Initialize project"` → Setup Claude Code context

### Terminal Commands
- `"Git status"` → Version control
- `"List files"` → Directory contents
- `"Run tests"` → Execute test suites
- Any terminal command works!

## 🏗️ Architecture

```
iPhone Voice → Zulip → Claude Bot → tmux Sessions → Terminal/Claude Code
     ↓
📱 Natural speech processing
🤖 Command interpretation  
💻 Secure local execution
🔄 Session persistence
```

### Core Components
- **`claude_bot.py`** - Main Zulip integration and command routing
- **`session_manager.py`** - tmux session lifecycle management
- **`terminal_bridge.py`** - Command execution and Claude Code integration
- **`context_manager.py`** - File handling and session context
- **`manage_claude_bot.sh`** - Production-ready management script

## 🔧 Management

```bash
# Start/stop the bot
./manage_claude_bot.sh start
./manage_claude_bot.sh stop
./manage_claude_bot.sh restart

# Monitor activity
./manage_claude_bot.sh logs
./manage_claude_bot.sh tail

# Session management
./manage_claude_bot.sh sessions list
./manage_claude_bot.sh sessions clean

# Web interface
./manage_claude_bot.sh web
```

## 🔒 Security Features

- **Local Execution**: Bot runs on your machine, no cloud dependencies
- **Command Filtering**: Configurable whitelist/blacklist of allowed commands
- **Secret Protection**: API keys and credentials never transmitted
- **Session Isolation**: Each session operates in its own context
- **Audit Logging**: Complete activity tracking and monitoring

## 🎯 Use Cases

### Remote Development
- Debug production issues from your phone
- Quick status checks during meetings
- Emergency hotfixes while away from desk

### Accessibility
- Hands-free coding for enhanced accessibility
- Voice-first development workflow
- Reduced typing strain

### AI-Assisted Development
- Natural language code analysis
- Voice-controlled pair programming
- Contextual development assistance

### Team Collaboration
- Share development sessions via Zulip
- Voice-controlled code reviews
- Remote pair programming sessions

## 📚 Configuration

### Basic Configuration (`config.yaml`)
```yaml
zulip:
  site: "https://your-zulip.com"
  email: "your-bot@your-zulip.com"
  api_key: "your-api-key"

sessions:
  base_dir: "~/sessions"
  max_sessions: 10

security:
  allowed_commands: ["ls", "cd", "pwd", "git", "python"]
  blocked_commands: ["rm -rf", "sudo"]
```

### Advanced Features
- Custom voice command patterns
- Project-specific configurations
- Integration with existing development tools
- Webhook integrations for CI/CD

## 🚀 Roadmap

- [ ] **Multi-Platform Support**: Discord, Slack, Teams integration
- [ ] **Plugin System**: Custom voice command extensions
- [ ] **Team Features**: Shared development sessions
- [ ] **Mobile App**: Dedicated iOS/Android app
- [ ] **Cloud Deployment**: Optional hosted version
- [ ] **IDE Integration**: VS Code and other editor plugins

## 🤝 Contributing

We welcome contributions! This project opens entirely new possibilities for voice-controlled development.

### Development Setup
```bash
# Fork the repository
git clone https://github.com/your-username/claude-terminal-bot.git
cd claude-terminal-bot

# Create development environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Start development bot
./manage_claude_bot.sh start
```

### Areas for Contribution
- Voice command pattern recognition
- Additional platform integrations
- Security enhancements
- Performance optimizations
- Documentation improvements
- Mobile app development

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **Anthropic** for Claude Code and AI capabilities
- **Zulip** for excellent bot API and mobile apps
- **tmux** for robust session management
- The **open source community** for making this possible

## 📞 Support

- **📖 Documentation**: Check our [comprehensive guides](docs/)
- **🐛 Issues**: Report bugs on [GitHub Issues](https://github.com/v-odoo/claude-terminal-bot/issues)
- **💬 Community**: Join our [Zulip chat](https://claude-terminal-bot.zulipchat.com)
- **📧 Contact**: [your-email@example.com](mailto:your-email@example.com)

---

**🎤 Transform your mobile device into the ultimate development controller!**

*Made with ❤️ for the future of voice-controlled programming*
