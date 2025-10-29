#!/bin/bash
# Pre-Security Update Backup Script
# This script creates a complete backup before applying security updates

set -e  # Exit on error

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$HOME/backups/pre-security-update-$TIMESTAMP"
SERVER_IP=$(hostname -I | awk '{print $1}')

echo "=========================================="
echo "Pre-Security Update Backup Script"
echo "=========================================="
echo "Timestamp: $TIMESTAMP"
echo "Server IP: $SERVER_IP"
echo "Backup Directory: $BACKUP_DIR"
echo ""

# Create backup directory
echo "Creating backup directory..."
mkdir -p "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR/plus"
mkdir -p "$BACKUP_DIR/plusistanbul"
mkdir -p "$BACKUP_DIR/docker"
mkdir -p "$BACKUP_DIR/git"

# Backup Plus project configurations
echo ""
echo "Backing up Plus project configurations..."
if [ -d "$HOME/plus" ]; then
    cp -r "$HOME/plus/docker-compose.yml" "$BACKUP_DIR/plus/" 2>/dev/null || true
    cp -r "$HOME/plus/docker-compose.production.yml" "$BACKUP_DIR/plus/" 2>/dev/null || true
    cp -r "$HOME/plus/.env" "$BACKUP_DIR/plus/" 2>/dev/null || true
    cp -r "$HOME/plus/.env.example" "$BACKUP_DIR/plus/" 2>/dev/null || true
    cp -r "$HOME/plus/nginx" "$BACKUP_DIR/plus/" 2>/dev/null || true
    cp -r "$HOME/plus/scripts" "$BACKUP_DIR/plus/" 2>/dev/null || true
    echo "✓ Plus configurations backed up"
else
    echo "⚠ Plus directory not found"
fi

# Backup PlusIstanbul project configurations
echo ""
echo "Backing up PlusIstanbul project configurations..."
if [ -d "$HOME/plusistanbul" ]; then
    cp -r "$HOME/plusistanbul/docker-compose.production-dev.yml" "$BACKUP_DIR/plusistanbul/" 2>/dev/null || true
    cp -r "$HOME/plusistanbul/docker-compose.production-secure.yml" "$BACKUP_DIR/plusistanbul/" 2>/dev/null || true
    cp -r "$HOME/plusistanbul/redis" "$BACKUP_DIR/plusistanbul/" 2>/dev/null || true
    cp -r "$HOME/plusistanbul/postgres" "$BACKUP_DIR/plusistanbul/" 2>/dev/null || true
    cp -r "$HOME/plusistanbul/nginx" "$BACKUP_DIR/plusistanbul/" 2>/dev/null || true
    cp -r "$HOME/plusistanbul/backend/.env" "$BACKUP_DIR/plusistanbul/" 2>/dev/null || true
    cp -r "$HOME/plusistanbul/backend/.env.example" "$BACKUP_DIR/plusistanbul/" 2>/dev/null || true
    cp -r "$HOME/plusistanbul/backend/env.production.example" "$BACKUP_DIR/plusistanbul/" 2>/dev/null || true
    echo "✓ PlusIstanbul configurations backed up"
else
    echo "⚠ PlusIstanbul directory not found"
fi

# Backup Docker state
echo ""
echo "Backing up Docker state..."
docker ps -a > "$BACKUP_DIR/docker/containers.txt" 2>/dev/null || true
docker images > "$BACKUP_DIR/docker/images.txt" 2>/dev/null || true
docker network ls > "$BACKUP_DIR/docker/networks.txt" 2>/dev/null || true
docker volume ls > "$BACKUP_DIR/docker/volumes.txt" 2>/dev/null || true
echo "✓ Docker state backed up"

# Backup Docker network configurations
echo ""
echo "Backing up Docker network details..."
docker network inspect istanbulplus_network > "$BACKUP_DIR/docker/network_istanbulplus.json" 2>/dev/null || true
docker network inspect peykan_internal > "$BACKUP_DIR/docker/network_peykan_internal.json" 2>/dev/null || true
docker network inspect peykan_external > "$BACKUP_DIR/docker/network_peykan_external.json" 2>/dev/null || true
docker network inspect shared_network > "$BACKUP_DIR/docker/network_shared.json" 2>/dev/null || true
echo "✓ Docker network details backed up"

# Export Docker volumes (data backup)
echo ""
echo "Backing up Docker volumes (this may take a while)..."
docker run --rm -v plus_redis_data:/data -v "$BACKUP_DIR/docker":/backup alpine tar czf /backup/plus_redis_data.tar.gz -C /data . 2>/dev/null || true
docker run --rm -v peykan_redis_data:/data -v "$BACKUP_DIR/docker":/backup alpine tar czf /backup/peykan_redis_data.tar.gz -C /data . 2>/dev/null || true
echo "✓ Docker volumes backed up"

# Save git status
echo ""
echo "Saving git status..."
if [ -d "$HOME/plus/.git" ]; then
    cd "$HOME/plus"
    git status > "$BACKUP_DIR/git/plus_git_status.txt" 2>/dev/null || true
    git log -1 > "$BACKUP_DIR/git/plus_git_last_commit.txt" 2>/dev/null || true
    git diff > "$BACKUP_DIR/git/plus_git_diff.txt" 2>/dev/null || true
    git branch -a > "$BACKUP_DIR/git/plus_git_branches.txt" 2>/dev/null || true
fi

if [ -d "$HOME/plusistanbul/.git" ]; then
    cd "$HOME/plusistanbul"
    git status > "$BACKUP_DIR/git/plusistanbul_git_status.txt" 2>/dev/null || true
    git log -1 > "$BACKUP_DIR/git/plusistanbul_git_last_commit.txt" 2>/dev/null || true
    git diff > "$BACKUP_DIR/git/plusistanbul_git_diff.txt" 2>/dev/null || true
    git branch -a > "$BACKUP_DIR/git/plusistanbul_git_branches.txt" 2>/dev/null || true
fi
echo "✓ Git status saved"

# Create backup summary
echo ""
echo "Creating backup summary..."
cat > "$BACKUP_DIR/BACKUP_INFO.txt" << EOF
Backup Information
==================
Date: $(date)
Server IP: $SERVER_IP
Hostname: $(hostname)
Backup Directory: $BACKUP_DIR

Purpose: Pre-security update backup before fixing Redis vulnerability (BSI report)

Contents:
- Plus project configurations (docker-compose, .env, nginx)
- PlusIstanbul project configurations (docker-compose, .env, redis, postgres, nginx)
- Docker state (containers, images, networks, volumes)
- Docker network configurations
- Docker volume data (Redis data)
- Git status and diffs for both projects

Restore Instructions:
To restore configurations, copy files from this backup to their original locations.
To restore Docker volumes, use:
  docker run --rm -v plus_redis_data:/data -v $BACKUP_DIR/docker:/backup alpine tar xzf /backup/plus_redis_data.tar.gz -C /data

Security Note:
This backup contains sensitive information including .env files with passwords.
Keep this backup secure and delete after security updates are verified.
EOF

echo "✓ Backup summary created"

# Calculate backup size
echo ""
echo "Calculating backup size..."
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "✓ Backup size: $BACKUP_SIZE"

# Create compressed archive
echo ""
echo "Creating compressed archive..."
cd "$HOME/backups"
tar czf "pre-security-update-$TIMESTAMP.tar.gz" "pre-security-update-$TIMESTAMP"
ARCHIVE_SIZE=$(du -sh "pre-security-update-$TIMESTAMP.tar.gz" | cut -f1)
echo "✓ Compressed archive created: pre-security-update-$TIMESTAMP.tar.gz ($ARCHIVE_SIZE)"

echo ""
echo "=========================================="
echo "Backup completed successfully!"
echo "=========================================="
echo "Backup location: $BACKUP_DIR"
echo "Archive location: $HOME/backups/pre-security-update-$TIMESTAMP.tar.gz"
echo "Backup size: $BACKUP_SIZE"
echo "Archive size: $ARCHIVE_SIZE"
echo ""
echo "IMPORTANT: Keep this backup until security updates are verified!"
echo ""
