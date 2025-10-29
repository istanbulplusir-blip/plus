#!/bin/bash
# Commit and Push Current State Script
# This script commits all current changes before security updates

set -e  # Exit on error

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
COMMIT_MESSAGE="Pre-security update commit - $TIMESTAMP

This commit saves the current state before applying Redis security hardening.
BSI Germany reported Redis vulnerability (exposed without authentication).

Changes include:
- Current docker-compose configurations
- Current environment configurations
- Current nginx configurations
- All recent feature developments

Next steps: Apply security updates to fix Redis vulnerability"

echo "=========================================="
echo "Commit and Push Current State"
echo "=========================================="
echo "Timestamp: $TIMESTAMP"
echo ""

# Function to commit and push a project
commit_and_push_project() {
    local project_dir=$1
    local project_name=$2
    
    echo ""
    echo "Processing $project_name project..."
    echo "----------------------------------------"
    
    if [ ! -d "$project_dir" ]; then
        echo "⚠ Directory not found: $project_dir"
        return 1
    fi
    
    cd "$project_dir"
    
    # Check if it's a git repository
    if [ ! -d ".git" ]; then
        echo "⚠ Not a git repository: $project_dir"
        return 1
    fi
    
    # Get current branch
    CURRENT_BRANCH=$(git branch --show-current)
    echo "Current branch: $CURRENT_BRANCH"
    
    # Check if there are changes
    if git diff-index --quiet HEAD -- 2>/dev/null; then
        echo "✓ No changes to commit"
        return 0
    fi
    
    # Show status
    echo ""
    echo "Git status:"
    git status --short
    
    # Add all changes
    echo ""
    echo "Adding all changes..."
    git add -A
    
    # Commit
    echo ""
    echo "Committing changes..."
    git commit -m "$COMMIT_MESSAGE"
    
    # Push
    echo ""
    echo "Pushing to remote..."
    if git push origin "$CURRENT_BRANCH"; then
        echo "✓ Successfully pushed to origin/$CURRENT_BRANCH"
    else
        echo "⚠ Failed to push. You may need to push manually."
        echo "  Command: git push origin $CURRENT_BRANCH"
    fi
    
    # Show last commit
    echo ""
    echo "Last commit:"
    git log -1 --oneline
    
    return 0
}

# Commit and push Plus project
commit_and_push_project "$HOME/plus" "Plus"

# Commit and push PlusIstanbul project
commit_and_push_project "$HOME/plusistanbul" "PlusIstanbul"

echo ""
echo "=========================================="
echo "Commit and Push Completed!"
echo "=========================================="
echo ""
echo "Both projects have been committed and pushed."
echo "You can now proceed with security updates."
echo ""
