#!/bin/bash

# Istanbul Plus Security Hardening Script
# This script implements security best practices for production deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root for security hardening"
fi

log "Starting security hardening for Istanbul Plus..."

# 1. System Updates
log "Updating system packages..."
apt update && apt upgrade -y

# 2. Firewall Configuration
log "Configuring UFW firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (be careful with this)
ufw allow 22/tcp comment 'SSH'

# Allow HTTP and HTTPS
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

# Allow Docker ports (if needed for external access)
# ufw allow 8000/tcp comment 'Peykan Tourism'
# ufw allow 8001/tcp comment 'Istanbul Plus'

# Enable firewall
ufw --force enable

# 3. SSH Hardening
log "Hardening SSH configuration..."
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

cat > /etc/ssh/sshd_config << 'EOF'
# SSH Hardening Configuration
Port 22
Protocol 2
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PermitEmptyPasswords no
MaxAuthTries 3
MaxSessions 2
ClientAliveInterval 300
ClientAliveCountMax 2
LoginGraceTime 60
AllowUsers istanbulplus
Banner /etc/ssh/banner
EOF

# Create SSH banner
cat > /etc/ssh/banner << 'EOF'
***************************************************************************
                    AUTHORIZED ACCESS ONLY
***************************************************************************
This system is for the use of authorized users only. Individuals using
this computer system without authority, or in excess of their authority,
are subject to having all of their activities on this system monitored
and recorded by system personnel.

In the course of monitoring individuals improperly using this system,
or in the course of system maintenance, the activities of authorized
users may also be monitored.

Anyone using this system expressly consents to such monitoring and is
advised that if such monitoring reveals possible evidence of criminal
activity, system personnel may provide the evidence of such monitoring
to law enforcement officials.
***************************************************************************
EOF

systemctl restart sshd

# 4. Fail2Ban Configuration
log "Installing and configuring Fail2Ban..."
apt install -y fail2ban

cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10

[django-auth]
enabled = true
filter = django-auth
port = http,https
logpath = /var/log/istanbulplus/security.log
maxretry = 5
EOF

# Create Django auth filter
cat > /etc/fail2ban/filter.d/django-auth.conf << 'EOF'
[Definition]
failregex = ^.*Authentication failed for user .* from <HOST>.*$
            ^.*Failed login attempt from <HOST>.*$
            ^.*Rate limit exceeded for <HOST>.*$
ignoreregex =
EOF

systemctl enable fail2ban
systemctl start fail2ban

# 5. System Hardening
log "Applying system hardening..."

# Disable unnecessary services
systemctl disable bluetooth
systemctl disable cups
systemctl disable avahi-daemon

# Configure kernel parameters
cat >> /etc/sysctl.conf << 'EOF'

# Security hardening
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv4.ip_forward = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.tcp_syncookies = 1
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0
EOF

sysctl -p

# 6. File Permissions
log "Setting secure file permissions..."

# Secure log files
chmod 640 /var/log/istanbulplus/*.log 2>/dev/null || true
chown istanbulplus:istanbulplus /var/log/istanbulplus/*.log 2>/dev/null || true

# Secure configuration files
chmod 600 /etc/ssh/sshd_config
chmod 600 /etc/fail2ban/jail.local

# 7. Docker Security
log "Configuring Docker security..."

# Create Docker daemon configuration
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "live-restore": true,
  "userland-proxy": false,
  "no-new-privileges": true
}
EOF

# 8. Application Security
log "Configuring application security..."

# Create security monitoring script
cat > /usr/local/bin/security-monitor.sh << 'EOF'
#!/bin/bash
# Security monitoring script

LOG_FILE="/var/log/security-monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Check for failed login attempts
FAILED_LOGINS=$(grep "Failed password" /var/log/auth.log | grep "$(date '+%b %d')" | wc -l)
if [ $FAILED_LOGINS -gt 10 ]; then
    echo "$DATE: WARNING - High number of failed login attempts: $FAILED_LOGINS" >> $LOG_FILE
fi

# Check for suspicious network activity
CONNECTIONS=$(netstat -an | grep :80 | wc -l)
if [ $CONNECTIONS -gt 1000 ]; then
    echo "$DATE: WARNING - High number of HTTP connections: $CONNECTIONS" >> $LOG_FILE
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "$DATE: WARNING - High disk usage: $DISK_USAGE%" >> $LOG_FILE
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ $MEMORY_USAGE -gt 90 ]; then
    echo "$DATE: WARNING - High memory usage: $MEMORY_USAGE%" >> $LOG_FILE
fi
EOF

chmod +x /usr/local/bin/security-monitor.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/security-monitor.sh") | crontab -

# 9. Backup Security
log "Configuring backup security..."

# Create secure backup script
cat > /usr/local/bin/secure-backup.sh << 'EOF'
#!/bin/bash
# Secure backup script

BACKUP_DIR="/backups/istanbulplus"
DATE=$(date +%Y%m%d_%H%M%S)

# Create encrypted backup
tar -czf - /var/log/istanbulplus/ | gpg --symmetric --cipher-algo AES256 --output $BACKUP_DIR/logs_$DATE.tar.gz.gpg

# Set secure permissions
chmod 600 $BACKUP_DIR/logs_$DATE.tar.gz.gpg
chown istanbulplus:istanbulplus $BACKUP_DIR/logs_$DATE.tar.gz.gpg

# Clean old backups (older than 30 days)
find $BACKUP_DIR -name "*.gpg" -mtime +30 -delete
EOF

chmod +x /usr/local/bin/secure-backup.sh

# 10. Log Monitoring
log "Setting up log monitoring..."

# Create log analysis script
cat > /usr/local/bin/log-analyzer.sh << 'EOF'
#!/bin/bash
# Log analysis script

LOG_DIR="/var/log/istanbulplus"
ALERT_EMAIL="admin@istanbulplus.ir"

# Check for security events
SECURITY_EVENTS=$(grep -i "security\|attack\|hack\|brute" $LOG_DIR/*.log | wc -l)
if [ $SECURITY_EVENTS -gt 0 ]; then
    echo "Security events detected: $SECURITY_EVENTS" | mail -s "Security Alert" $ALERT_EMAIL
fi

# Check for error patterns
ERROR_PATTERNS=$(grep -i "error\|exception\|critical" $LOG_DIR/*.log | wc -l)
if [ $ERROR_PATTERNS -gt 100 ]; then
    echo "High number of errors detected: $ERROR_PATTERNS" | mail -s "Error Alert" $ALERT_EMAIL
fi
EOF

chmod +x /usr/local/bin/log-analyzer.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "0 */6 * * * /usr/local/bin/log-analyzer.sh") | crontab -

# 11. Network Security
log "Configuring network security..."

# Install and configure AIDE (Advanced Intrusion Detection Environment)
apt install -y aide
aideinit
mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Create AIDE check script
cat > /usr/local/bin/aide-check.sh << 'EOF'
#!/bin/bash
# AIDE integrity check

aide --check > /var/log/aide-check.log 2>&1
if [ $? -ne 0 ]; then
    echo "AIDE integrity check failed. Check /var/log/aide-check.log" | mail -s "AIDE Alert" admin@istanbulplus.ir
fi
EOF

chmod +x /usr/local/bin/aide-check.sh

# Add to crontab (daily check)
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/aide-check.sh") | crontab -

# 12. Final Security Checks
log "Performing final security checks..."

# Check for open ports
log "Open ports:"
ss -tuln | grep LISTEN

# Check running services
log "Running services:"
systemctl list-units --type=service --state=running | grep -E "(ssh|nginx|docker|fail2ban)"

# Check firewall status
log "Firewall status:"
ufw status verbose

log "Security hardening completed successfully!"
log "Please review the configuration and test all services."
log "Remember to:"
log "1. Test SSH access with your key"
log "2. Verify firewall rules"
log "3. Check application functionality"
log "4. Monitor logs for any issues"
log "5. Update this script as needed for your environment"
