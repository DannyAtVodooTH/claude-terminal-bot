#!/usr/bin/env python3
"""
Setup and test script for Claude Terminal Bot
"""

import os
import sys
import subprocess
import yaml
from pathlib import Path


def check_requirements():
    """Check if all requirements are met."""
    print("Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ required")
        return False
    print("✅ Python version OK")
    
    # Check tmux
    try:
        subprocess.run(["tmux", "-V"], check=True, capture_output=True)
        print("✅ tmux installed")
    except subprocess.CalledProcessError:
        print("❌ tmux not found. Install with: brew install tmux")
        return False
    
    # Check Claude Code
    try:
        subprocess.run(["claude_code", "--version"], check=True, capture_output=True)
        print("✅ Claude Code available")
    except subprocess.CalledProcessError:
        print("⚠️  Claude Code not found (optional)")
    
    return True


def install_dependencies():
    """Install Python dependencies."""
    print("\nInstalling Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def setup_directories():
    """Create necessary directories."""
    print("\nSetting up directories...")
    
    # Expand home directory
    sessions_dir = Path("~/sessions").expanduser()
    sessions_dir.mkdir(exist_ok=True)
    print(f"✅ Sessions directory: {sessions_dir}")
    
    # Secrets directory
    secrets_dir = Path("~/.secrets").expanduser()
    secrets_dir.mkdir(exist_ok=True)
    print(f"✅ Secrets directory: {secrets_dir}")
    
    return True


def test_basic_functionality():
    """Test basic components without Zulip."""
    print("\nTesting basic functionality...")
    
    try:
        # Test session manager
        sys.path.append('.')
        from session_manager import SessionManager
        from terminal_bridge import TerminalBridge
        from context_manager import ContextManager
        
        # Load config
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Expand paths
        config['sessions']['base_dir'] = os.path.expanduser(config['sessions']['base_dir'])
        
        # Test components
        session_manager = SessionManager(config['sessions'])
        terminal_bridge = TerminalBridge(config)
        context_manager = ContextManager(config['sessions']['base_dir'])
        
        print("✅ All components loaded successfully")
        
        # Test session creation
        session_id = session_manager.create_session("test-session", "test")
        print(f"✅ Test session created: {session_id}")
        
        # Test terminal command
        session = session_manager.sessions[session_id]
        result = terminal_bridge.execute_command("echo 'Hello from Claude Bot!'", session)
        print(f"✅ Terminal command executed: {result[:50]}...")
        
        # Cleanup test session
        session_manager.kill_session(session_id)
        print("✅ Test session cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False


def show_next_steps():
    """Show next steps for setup."""
    print("""
🎉 Setup completed successfully!

Next steps:

1. Set up Zulip bot:
   - Go to https://v-odoo.zulipchat.com
   - Create a bot account (Settings → Your bots → Add a new bot)
   - Copy the API key and update config.yaml

2. Update config.yaml:
   - Replace YOUR_API_KEY_HERE with your bot's API key
   - Adjust paths and settings as needed

3. Test the bot:
   python claude_bot.py

4. Test web interface:
   python web_interface.py
   Then visit http://localhost:8080

5. Send voice messages from iPhone:
   - Use Zulip mobile app
   - Use voice-to-text feature
   - Send commands like: /new-session "my-project"

Bot commands:
- /new-session "name" - Create new session
- /list-sessions - Show all sessions  
- /switch-session 001 - Switch to session
- /claude-start - Start Claude Code
- Any other text - Execute as terminal command

Enjoy your voice-controlled terminal! 🚀
""")


def main():
    """Main setup function."""
    print("Claude Terminal Bot Setup")
    print("=" * 40)
    
    if not check_requirements():
        sys.exit(1)
    
    if not install_dependencies():
        sys.exit(1)
    
    if not setup_directories():
        sys.exit(1)
    
    if not test_basic_functionality():
        sys.exit(1)
    
    show_next_steps()


if __name__ == "__main__":
    main()
