#!/bin/bash

# Fixed setup script for floatctl shell completions

echo "Setting up floatctl shell completions..."

# Detect the user's actual shell from SHELL environment variable
USER_SHELL=$(basename "$SHELL")
echo "Detected user shell: $USER_SHELL"

# Set RC file based on shell
case "$USER_SHELL" in
    zsh)
        RC_FILE="$HOME/.zshrc"
        COMPLETION_TYPE="zsh"
        ;;
    bash)
        RC_FILE="$HOME/.bashrc"
        COMPLETION_TYPE="bash"
        ;;
    *)
        echo "Unsupported shell: $USER_SHELL. Only bash and zsh are supported."
        exit 1
        ;;
esac

# Create completion directory
COMPLETION_DIR="$HOME/.config/floatctl"
mkdir -p "$COMPLETION_DIR"

# Generate completion script based on detected shell
echo "Generating $COMPLETION_TYPE completion script..."

if [ "$COMPLETION_TYPE" = "zsh" ]; then
    cat > "$COMPLETION_DIR/floatctl-complete.sh" << 'EOF'
# FloatCtl zsh completion script
if [ -n "$ZSH_VERSION" ]; then
    eval "$(_FLOATCTL_COMPLETE=zsh_source floatctl)"
fi
EOF
else
    cat > "$COMPLETION_DIR/floatctl-complete.sh" << 'EOF'
# FloatCtl bash completion script  
if [ -n "$BASH_VERSION" ]; then
    eval "$(_FLOATCTL_COMPLETE=bash_source floatctl)"
fi
EOF
fi

# Add to shell RC file if not already present
if ! grep -q "floatctl-complete.sh" "$RC_FILE" 2>/dev/null; then
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
echo ""
echo "Test completion with:"
echo "  floatctl <TAB><TAB>"