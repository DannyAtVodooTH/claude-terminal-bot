#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Configuration
BOT_NAME="claude-terminal-bot"
VENV_PATH="venv"
BOT_SCRIPT="claude_bot.py"
PID_FILE="claude_bot.pid"
LOG_FILE="claude_bot.log"
CONFIG_FILE="config.yaml"

# Function to kill existing bot processes
kill_bot() {
    echo "Stopping Claude Bot..."
    
    # Kill by PID file if it exists
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID
            sleep 2
            if ps -p $PID > /dev/null 2>&1; then
                echo "Force killing bot process..."
                kill -9 $PID
            fi
        fi
        rm -f "$PID_FILE"
    fi
    
    # Kill any remaining claude_bot processes
    pkill -f "$BOT_SCRIPT"
    sleep 1
    
    echo "Claude Bot stopped"
}

# Function to start the bot
start_bot() {
    # Check if config has API key
    if grep -q "YOUR_API_KEY_HERE" "$CONFIG_FILE" 2>/dev/null; then
        echo "❌ Error: Please update $CONFIG_FILE with your Zulip API key first!"
        echo "Visit https://v-odoo.zulipchat.com to create a bot and get API key"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_PATH" ]; then
        echo "❌ Error: Virtual environment not found at $VENV_PATH"
        echo "Run: python3 -m venv $VENV_PATH && source $VENV_PATH/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
    
    # Start the bot in the background
    echo "Starting Claude Terminal Bot..."
    nohup "$VENV_PATH/bin/python3" "$BOT_SCRIPT" > "$LOG_FILE" 2>&1 &
    
    # Get the PID of the new bot process
    BOT_PID=$!
    
    # Save the PID to a file
    echo $BOT_PID > "$PID_FILE"
    
    echo "✅ Claude Bot started with PID: $BOT_PID"
    echo "📄 Logs are being written to $LOG_FILE"
    echo "🔍 Use 'tail -f $LOG_FILE' to monitor activity"
}

# Function to check if bot is running
check_bot() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "✅ Claude Bot is running with PID: $PID"
            return 0
        else
            echo "❌ Claude Bot is not running (stale PID file found)"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        # Check if any claude_bot processes are running
        if pgrep -f "$BOT_SCRIPT" > /dev/null; then
            echo "⚠️  Claude Bot processes found but no PID file"
            return 2
        else
            echo "❌ Claude Bot is not running"
            return 1
        fi
    fi
}

# Function to show bot logs
show_logs() {
    local lines="${1:-50}"
    if [ -f "$LOG_FILE" ]; then
        echo "📄 Last $lines lines of Claude Bot logs:"
        echo "----------------------------------------"
        tail -n "$lines" "$LOG_FILE"
    else
        echo "❌ Log file not found: $LOG_FILE"
        exit 1
    fi
}

# Function to follow logs in real-time
follow_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "📄 Following Claude Bot logs (Press Ctrl+C to stop):"
        echo "----------------------------------------"
        tail -f "$LOG_FILE"
    else
        echo "❌ Log file not found: $LOG_FILE"
        exit 1
    fi
}

# Function to manage sessions
manage_sessions() {
    local action="$1"
    case "$action" in
        "list")
            echo "📋 Active Sessions:"
            find ~/sessions -name "session.json" -exec echo "Session {}" \; -exec cat {} \; 2>/dev/null | grep -E "(Session|\"id\"|\"name\")" || echo "No sessions found"
            ;;
        "clean")
            echo "🧹 Cleaning up orphaned tmux sessions..."
            # Kill tmux sessions that start with claude-session-
            tmux list-sessions 2>/dev/null | grep "claude-session-" | cut -d: -f1 | xargs -I {} tmux kill-session -t {} 2>/dev/null || true
            echo "✅ Cleanup complete"
            ;;
        *)
            echo "Usage: $0 sessions {list|clean}"
            echo "  list  - Show all active bot sessions"
            echo "  clean - Clean up orphaned tmux sessions"
            ;;
    esac
}

# Function to test bot setup
test_bot() {
    echo "🧪 Testing Claude Bot setup..."
    
    # Check Python and virtual environment
    if [ ! -d "$VENV_PATH" ]; then
        echo "❌ Virtual environment not found"
        return 1
    fi
    
    # Check config file
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "❌ Config file not found: $CONFIG_FILE"
        return 1
    fi
    
    # Check dependencies
    if ! "$VENV_PATH/bin/python3" -c "import zulip, yaml" 2>/dev/null; then
        echo "❌ Required dependencies not installed"
        echo "Run: source $VENV_PATH/bin/activate && pip install -r requirements.txt"
        return 1
    fi
    
    # Check tmux
    if ! command -v tmux >/dev/null 2>&1; then
        echo "❌ tmux not installed"
        echo "Run: brew install tmux"
        return 1
    fi
    
    echo "✅ All tests passed!"
    return 0
}

# Display help
show_help() {
    echo "🤖 Claude Terminal Bot Management Script"
    echo
    echo "Usage: $0 COMMAND [OPTIONS]"
    echo
    echo "Commands:"
    echo "  start                Start Claude Bot if not already running"
    echo "  restart              Stop and restart Claude Bot"
    echo "  stop                 Stop running Claude Bot"
    echo "  status               Check if Claude Bot is running"
    echo "  logs [LINES]         Show last N lines of logs (default: 50)"
    echo "  tail                 Follow logs in real-time"
    echo "  test                 Test bot setup and dependencies"
    echo "  sessions ACTION      Manage bot sessions (list|clean)"
    echo "  web                  Start web interface"
    echo
    echo "Examples:"
    echo "  $0 start             # Start the bot"
    echo "  $0 logs 100          # Show last 100 log lines"
    echo "  $0 tail              # Follow logs in real-time"
    echo "  $0 sessions list     # Show all active sessions"
    echo "  $0 sessions clean    # Clean up orphaned tmux sessions"
    echo
    echo "Voice Commands (via Zulip):"
    echo "  /new-session \"name\"   # Create new terminal session"
    echo "  /list-sessions        # Show active sessions"
    echo "  /switch-session 002   # Switch to session"
    echo "  /claude-start         # Start Claude Code"
}

# Function to start web interface
start_web() {
    echo "🌐 Starting Claude Bot Web Interface..."
    if [ ! -d "$VENV_PATH" ]; then
        echo "❌ Virtual environment not found"
        exit 1
    fi
    
    echo "📱 Web interface will be available at: http://localhost:8080"
    "$VENV_PATH/bin/python3" web_interface.py
}

# Main script
case "$1" in
    "start")
        if check_bot; then
            echo "⚠️  Claude Bot is already running"
        else
            start_bot
        fi
        ;;
    "restart")
        kill_bot
        sleep 1
        start_bot
        ;;
    "stop")
        kill_bot
        ;;
    "status")
        check_bot
        ;;
    "logs")
        show_logs "$2"
        ;;
    "tail")
        follow_logs
        ;;
    "test")
        test_bot
        ;;
    "sessions")
        manage_sessions "$2"
        ;;
    "web")
        start_web
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac
