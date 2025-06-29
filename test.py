#!/usr/bin/env python3
"""
Quick test runner for the Claude Bot
"""

import os
import sys

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        sys.path.append('.')
        import claude_bot
        import session_manager
        import terminal_bridge
        import context_manager
        import web_interface
        print("✅ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test config loading."""
    print("Testing config...")
    
    try:
        import yaml
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        required_keys = ['zulip', 'sessions', 'claude_code']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing config key: {key}")
        
        print("✅ Config loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def main():
    print("Claude Bot Quick Test")
    print("=" * 30)
    
    os.chdir('/Users/dgoo2308/git/claude-bot')
    
    if not test_imports():
        sys.exit(1)
    
    if not test_config():
        sys.exit(1)
    
    print("\n🎉 All tests passed!")
    print("Ready to run the bot with: python claude_bot.py")

if __name__ == "__main__":
    main()
