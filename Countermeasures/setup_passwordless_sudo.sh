#!/bin/bash
# Configure Passwordless Sudo for Countermeasures
# This allows iptables commands to run without password prompts

echo "========================================================================"
echo "Configuring Passwordless Sudo for SecIDS Countermeasures"
echo "========================================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script must be run as root (use sudo)"
    echo "Usage: sudo bash $0"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER="${SUDO_USER:-$USER}"

echo "Configuring for user: $ACTUAL_USER"
echo ""

# Create sudoers configuration file
SUDOERS_FILE="/etc/sudoers.d/secids-countermeasures"

cat > "$SUDOERS_FILE" << EOF
# SecIDS-CNN Countermeasure System - Passwordless iptables
# Created: $(date)
# Allows countermeasure system to manage iptables without password

# Allow iptables commands
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/sbin/iptables
$ACTUAL_USER ALL=(ALL) NOPASSWD: /sbin/iptables

# Specific commands for IP blocking
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/sbin/iptables -A INPUT -s * -j DROP
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/sbin/iptables -D INPUT -s * -j DROP
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/sbin/iptables -A INPUT -p tcp --dport * -j DROP
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/sbin/iptables -D INPUT -p tcp --dport * -j DROP
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/sbin/iptables -F
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/sbin/iptables -L
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/sbin/iptables -L -n -v
EOF

# Set correct permissions (must be 0440)
chmod 0440 "$SUDOERS_FILE"

# Verify syntax
if visudo -c -f "$SUDOERS_FILE" > /dev/null 2>&1; then
    echo "✅ Sudoers configuration created successfully"
    echo "   File: $SUDOERS_FILE"
    echo ""
    echo "Testing configuration..."
    
    # Test if it works
    sudo -u "$ACTUAL_USER" sudo iptables -L > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Passwordless sudo is working!"
        echo ""
        echo "You can now run countermeasures without password prompts:"
        echo "  python3 Countermeasures/passive_ui.py"
        echo "  python3 Countermeasures/active_ui.py"
    else
        echo "⚠️  Test failed, but configuration is installed"
        echo "   You may need to log out and back in"
    fi
else
    echo "❌ Sudoers syntax error, removing configuration"
    rm -f "$SUDOERS_FILE"
    exit 1
fi

echo ""
echo "========================================================================"
echo "Configuration Complete!"
echo "========================================================================"
echo ""
echo "To remove this configuration later, run:"
echo "  sudo rm $SUDOERS_FILE"
echo ""
