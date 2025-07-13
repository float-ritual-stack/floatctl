#!/bin/bash

# Setup script for floatctl shell completions

echo "Setting up floatctl shell completions..."

# Detect shell
if [ -n "$ZSH_VERSION" ]; then
    SHELL_TYPE="zsh"
    RC_FILE="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_TYPE="bash"
    RC_FILE="$HOME/.bashrc"
else
    echo "Unsupported shell. Only bash and zsh are supported."
    exit 1
fi

echo "Detected shell: $SHELL_TYPE"

# Create completion directory
COMPLETION_DIR="$HOME/.config/floatctl"
mkdir -p "$COMPLETION_DIR"

# Generate completion script
echo "Generating completion script..."
cat > "$COMPLETION_DIR/floatctl-complete.sh" << 'EOF'
# FloatCtl completion script
if [ -n "$ZSH_VERSION" ]; then
    eval "$(_FLOATCTL_COMPLETE=zsh_source floatctl)"
elif [ -n "$BASH_VERSION" ]; then
    eval "$(_FLOATCTL_COMPLETE=bash_source floatctl)"
fi
EOF

# Add to shell RC file if not already present
if ! grep -q "floatctl-complete.sh" "$RC_FILE"; then
    echo "" >> "$RC_FILE"
    echo "# FloatCtl completions" >> "$RC_FILE"
    echo "[ -f \"$COMPLETION_DIR/floatctl-complete.sh\" ] && source \"$COMPLETION_DIR/floatctl-complete.sh\"" >> "$RC_FILE"
    echo "Added completion source to $RC_FILE"
else
    echo "Completion already configured in $RC_FILE"
fi

echo ""
echo "Setup complete! To activate completions:"
echo "  source $RC_FILE"
echo ""
echo "Or restart your terminal."