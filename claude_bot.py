#!/usr/bin/env python3
"""
Claude Terminal Bot - Main Application

Voice-controlled terminal sessions via Zulip integration.
Allows iPhone voice-to-text commands to control terminal and Claude Code.
"""

import os
import sys
import yaml
import logging
import asyncio
from pathlib import Path

import zulip
from session_manager import SessionManager
from terminal_bridge import TerminalBridge
from context_manager import ContextManager


class ClaudeBot:
    def __init__(self, config_path="config.yaml"):
        """Initialize the Claude Terminal Bot."""
        self.config = self.load_config(config_path)
        self.setup_logging()
        
        # Initialize components
        self.session_manager = SessionManager(self.config['sessions'])
        self.terminal_bridge = TerminalBridge(self.config)
        self.context_manager = ContextManager(self.config['sessions']['base_dir'])
        
        # Message deduplication
        self.processed_messages = set()
        
        # Initialize Zulip client
        self.zulip_client = self.setup_zulip()
        
        self.logger.info("Claude Bot initialized successfully")

    def load_config(self, config_path):
        """Load configuration from YAML file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Expand home directory paths
        config['sessions']['base_dir'] = os.path.expanduser(config['sessions']['base_dir'])
        if 'odoo' in config:
            config['odoo']['config_dir'] = os.path.expanduser(config['odoo']['config_dir'])
            config['odoo']['git_dir'] = os.path.expanduser(config['odoo']['git_dir'])
        
        return config

    def setup_logging(self):
        """Configure logging."""
        log_level = self.config.get('logging', {}).get('level', 'INFO')
        log_file = self.config.get('logging', {}).get('file')
        
        if log_file:
            log_file = os.path.expanduser(log_file)
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_file) if log_file else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_zulip(self):
        """Initialize Zulip client."""
        try:
            client = zulip.Client(
                site=self.config['zulip']['site'],
                email=self.config['zulip']['email'],
                api_key=self.config['zulip']['api_key']
            )
            
            # Test connection
            result = client.get_profile()
            if result['result'] == 'success':
                self.logger.info(f"Connected to Zulip as {result['email']}")
                return client
            else:
                raise Exception(f"Zulip connection failed: {result}")
                
        except Exception as e:
            self.logger.error(f"Failed to connect to Zulip: {e}")
            raise

    def handle_message(self, message):
        """Process incoming Zulip messages."""
        try:
            # Deduplicate messages
            message_id = message.get('id')
            if message_id in self.processed_messages:
                return
            self.processed_messages.add(message_id)
            
            content = message['content'].strip()
            # Remove HTML tags from content
            import re
            content = re.sub(r'<[^>]+>', '', content).strip()
            
            sender = message['sender_email']
            message_type = message.get('type', 'stream')
            
            if message_type == 'private':
                # Private message
                topic = f"pm-{sender.split('@')[0]}"
                stream = None  # No stream for private messages
                self.logger.info(f"Private message from {sender}: {content}")
            else:
                # Stream message
                topic = message.get('subject', 'general')
                stream = message.get('display_recipient', 'general')
                self.logger.info(f"Stream message from {sender} in {stream}#{topic}: {content}")
            
            # Skip messages from the bot itself
            if sender == self.config['zulip']['email']:
                return
            
            # Route message based on content
            if content.startswith('/'):
                response = self.handle_command(content, topic, sender)
            elif self.is_natural_command(content):
                # Convert natural language to bot command
                bot_command = self.convert_natural_command(content)
                response = self.handle_command(bot_command, topic, sender)
            else:
                response = self.handle_terminal_input(content, topic, sender)
            
            # Send response back to Zulip
            if response:
                if message_type == 'private':
                    self.send_private_message(response, sender)
                else:
                    self.send_message(response, topic, stream)
                
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            if message_type == 'private':
                self.send_private_message(f"Error: {str(e)}", sender)
            else:
                self.send_message(f"Error: {str(e)}", topic, stream)

    def handle_command(self, command, topic, sender):
        """Handle bot commands starting with /."""
        parts = command[1:].split()
        cmd = parts[0] if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        
        try:
            if cmd == "new-session":
                name = " ".join(args) if args else f"session-{len(self.session_manager.sessions) + 1}"
                session_id = self.session_manager.create_session(name, topic)
                return f"Created session {session_id}: {name}"
                
            elif cmd == "list-sessions":
                sessions = self.session_manager.list_sessions()
                if not sessions:
                    return "No active sessions"
                return "Active sessions:\n" + "\n".join([f"- {s['id']}: {s['name']}" for s in sessions])
                
            elif cmd == "switch-session":
                if not args:
                    return "Usage: /switch-session <session_id>"
                session_id = args[0]
                if self.session_manager.switch_session(session_id, topic):
                    return f"Switched to session {session_id}"
                else:
                    return f"Session {session_id} not found"
                    
            elif cmd == "claude-start":
                current_session = self.session_manager.get_current_session(topic)
                if current_session:
                    result = self.terminal_bridge.start_claude_code(current_session)
                    return result
                else:
                    return "No active session. Use /new-session first."
            
            elif cmd == "working-dir":
                if not args:
                    return "Usage: /working-dir <path>"
                current_session = self.session_manager.get_current_session(topic)
                if current_session:
                    new_dir = " ".join(args)
                    # Expand shortcuts
                    if new_dir.startswith("git/"):
                        new_dir = f"/Users/dgoo2308/git/{new_dir[4:]}"
                    elif new_dir == "odoo18":
                        new_dir = "/Users/dgoo2308/git/odoo18"
                    
                    if self.session_manager.set_working_directory(current_session['id'], new_dir):
                        return f"✅ Working directory changed to: {new_dir}"
                    else:
                        return f"❌ Directory not found: {new_dir}"
                else:
                    return "No active session. Use /new-session first."
                    
            elif cmd == "help":
                return self.get_help_text()
                
            else:
                return f"Unknown command: {cmd}. Use /help for available commands."
                
        except Exception as e:
            self.logger.error(f"Command error: {e}")
            return f"Command failed: {str(e)}"

    def handle_terminal_input(self, content, topic, sender):
        """Handle regular messages as terminal input."""
        try:
            current_session = self.session_manager.get_current_session(topic)
            if not current_session:
                return "No active session. Use /new-session to create one."
            
            # Execute command in terminal
            result = self.terminal_bridge.execute_command(content, current_session)
            return f"```\n{result}\n```" if result else "Command executed (no output)"
            
        except Exception as e:
            self.logger.error(f"Terminal execution error: {e}")
            return f"Execution failed: {str(e)}"

    def send_message(self, content, topic="general", stream="general"):
        """Send message to Zulip."""
        try:
            result = self.zulip_client.send_message({
                "type": "stream",
                "to": stream,  # Stream name
                "topic": topic,
                "content": content
            })
            if result.get('result') != 'success':
                self.logger.error(f"Failed to send message: {result}")
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")

    def send_private_message(self, content, recipient):
        """Send private message to a user."""
        try:
            result = self.zulip_client.send_message({
                "type": "private",
                "to": [recipient],
                "content": content
            })
            if result.get('result') != 'success':
                self.logger.error(f"Failed to send private message: {result}")
        except Exception as e:
            self.logger.error(f"Failed to send private message: {e}")

    def is_natural_command(self, content):
        """Check if content is a natural language bot command."""
        content_lower = content.lower()
        
        natural_commands = [
            "start claude", "claude start", "start claude code",
            "stop claude", "claude stop", "stop claude code",
            "list sessions", "show sessions", "list all sessions",
            "new session", "create session", "create new session",
            "switch session", "change session", "switch to session",
            "help", "show help", "bot help"
        ]
        
        return any(cmd in content_lower for cmd in natural_commands)

    def convert_natural_command(self, content):
        """Convert natural language to bot command."""
        content_lower = content.lower()
        
        # Claude Code commands
        if any(phrase in content_lower for phrase in ["start claude", "claude start"]):
            return "/claude-start"
        elif any(phrase in content_lower for phrase in ["stop claude", "claude stop"]):
            return "/claude-stop"
        
        # Working directory commands
        elif "change directory" in content_lower or "cd " in content:
            # Extract directory path
            import re
            if "cd " in content:
                match = re.search(r'cd\s+([^\s]+)', content)
                if match:
                    return f"/working-dir {match.group(1)}"
            return content  # Pass through as terminal command
        
        # Session commands
        elif any(phrase in content_lower for phrase in ["list sessions", "show sessions"]):
            return "/list-sessions"
        elif "new session" in content_lower or "create session" in content_lower:
            # Extract session name if provided
            import re
            match = re.search(r'(?:new|create) session(?:\s+(?:called\s+)?["\']?([^"\']+)["\']?)?', content_lower)
            if match and match.group(1):
                return f'/new-session "{match.group(1).strip()}"'
            else:
                return "/new-session"
        elif "switch" in content_lower and "session" in content_lower:
            # Extract session number/name
            import re
            match = re.search(r'session\s+(\w+)', content_lower)
            if match:
                return f"/switch-session {match.group(1)}"
            else:
                return "/list-sessions"  # Show sessions if unclear
        
        # Help
        elif "help" in content_lower:
            return "/help"
        
        # Default fallback
        return "/help"

    def get_help_text(self):
        """Return help text with available commands."""
        return """
**Claude Terminal Bot Commands:**

**Session Management:**
- `/new-session [name]` - Create a new terminal session
- `/list-sessions` - Show all active sessions  
- `/switch-session <id>` - Switch to a session
- `/sleep-session <id>` - Background a session
- `/kill-session <id>` - Terminate a session

**Claude Code:**
- `/claude-start` - Initialize Claude Code in current session
- `/claude-stop` - Stop Claude Code
- `/claude-status` - Check Claude Code status

**Context:**
- `/context upload <file>` - Upload file to session context
- `/context list` - Show session context files
- `/working-dir <path>` - Change session working directory

**Other:**
- `/help` - Show this help message

Send any other message to execute as a terminal command.
"""

    def run(self):
        """Start the bot and listen for messages."""
        self.logger.info("Starting Claude Bot...")
        
        # Register message handler
        self.zulip_client.call_on_each_message(self.handle_message)
        
        self.logger.info("Bot is running. Press Ctrl+C to stop.")


def main():
    """Main entry point."""
    try:
        bot = ClaudeBot()
        bot.run()
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Bot failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
