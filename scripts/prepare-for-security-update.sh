#!/bin/bash
# Master Preparation Script for Security Updates
# This script performs all necessary preparations before security updates

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "Security Update Preparation"
echo "=========================================="
echo "This script will:"
echo "1. Create a complete backup of current state"
echo "2. Commit all changes in both projects"
echo "3. Push commits to remote repositories"
echo ""
echo "Timestamp: $TIMESTAMP"
echo ""

# Ask for confirmation
read -p "Do you want to proceed? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted by user."
    exit 0
fi

echo ""
echo "=========================================="
echo "Step 1: Creating Backup"
echo "=========================================="
bash "$SCRIPT_DIR/pre-security-backup.sh"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Backup failed! Aborting."
    exit 1
fi

echo ""
echo "=========================================="
echo "Step 2: Committing and Pushing Changes"
echo "=========================================="
bash "$SCRIPT_DIR/commit-and-push-current-state.sh"

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠ Commit/Push had issues, but backup is complete."
    echo "You can manually commit and push later if needed."
fi

echo ""
echo "=========================================="
echo "Preparation Complete!"
echo "=========================================="
echo ""
echo "✓ Backup created: $HOME/backups/pre-security-update-$TIMESTAMP"
echo "✓ Changes committed and pushed (if successful)"
echo ""
echo "You are now ready to apply security updates."
echo ""
echo "Next steps:"
echo "1. Review the security spec: .kiro/specs/redis-security-hardening/"
echo "2. Start implementing tasks from tasks.md"
echo "3. Begin with Task 1: Create security utilities"
echo ""
echo "IMPORTANT: Keep the backup until security updates are verified!"
echo ""
