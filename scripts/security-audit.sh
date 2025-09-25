#!/bin/bash

# Istanbul Plus Security Audit Script
# This script performs comprehensive security checks

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
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Security audit results
AUDIT_RESULTS="/tmp/security-audit-$(date +%Y%m%d_%H%M%S).txt"
ISSUES_FOUND=0

# Function to add result
add_result() {
    local status=$1
    local message=$2
    echo "[$status] $message" >> $AUDIT_RESULTS
    
    if [ "$status" = "FAIL" ]; then
        error "$message"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    elif [ "$status" = "WARN" ]; then
        warn "$message"
    else
        log "$message"
    fi
}

log "Starting security audit for Istanbul Plus..."

# 1. System Information
info "=== SYSTEM INFORMATION ==="
add_result "INFO" "Hostname: $(hostname)"
add_result "INFO" "OS: $(lsb_release -d | cut -f2)"
add_result "INFO" "Kernel: $(uname -r)"
add_result "INFO" "Uptime: $(uptime -p)"

# 2. User Security
info "=== USER SECURITY ==="

# Check for root login
if grep -q "^PermitRootLogin yes" /etc/ssh/sshd_config 2>/dev/null; then
    add_result "FAIL" "Root login is enabled in SSH"
else
    add_result "PASS" "Root login is disabled in SSH"
fi

# Check for password authentication
if grep -q "^PasswordAuthentication yes" /etc/ssh/sshd_config 2>/dev/null; then
    add_result "WARN" "Password authentication is enabled in SSH"
else
    add_result "PASS" "Password authentication is disabled in SSH"
fi

# Check for empty passwords
if awk -F: '($2 == "") {print $1}' /etc/shadow 2>/dev/null | grep -q .; then
    add_result "FAIL" "Users with empty passwords found"
else
    add_result "PASS" "No users with empty passwords"
fi

# Check for users with UID 0
if awk -F: '($3 == 0) {print $1}' /etc/passwd | grep -v root | grep -q .; then
    add_result "FAIL" "Multiple users with UID 0 found"
else
    add_result "PASS" "Only root has UID 0"
fi

# 3. Network Security
info "=== NETWORK SECURITY ==="

# Check firewall status
if ufw status | grep -q "Status: active"; then
    add_result "PASS" "UFW firewall is active"
else
    add_result "FAIL" "UFW firewall is not active"
fi

# Check for listening ports
LISTENING_PORTS=$(ss -tuln | grep LISTEN | wc -l)
add_result "INFO" "Number of listening ports: $LISTENING_PORTS"

# Check for suspicious ports
if ss -tuln | grep -q ":23 "; then
    add_result "FAIL" "Telnet port (23) is open"
fi

if ss -tuln | grep -q ":21 "; then
    add_result "WARN" "FTP port (21) is open"
fi

if ss -tuln | grep -q ":25 "; then
    add_result "WARN" "SMTP port (25) is open"
fi

# 4. Service Security
info "=== SERVICE SECURITY ==="

# Check for unnecessary services
UNNECESSARY_SERVICES=("telnet" "ftp" "rsh" "rlogin" "rexec" "finger" "talk" "ntalk")
for service in "${UNNECESSARY_SERVICES[@]}"; do
    if systemctl is-active --quiet $service 2>/dev/null; then
        add_result "FAIL" "Unnecessary service $service is running"
    fi
done

# Check for enabled services
ENABLED_SERVICES=$(systemctl list-unit-files --type=service --state=enabled | wc -l)
add_result "INFO" "Number of enabled services: $ENABLED_SERVICES"

# 5. File System Security
info "=== FILE SYSTEM SECURITY ==="

# Check for world-writable files
WORLD_WRITABLE=$(find / -type f -perm -002 2>/dev/null | wc -l)
if [ $WORLD_WRITABLE -gt 0 ]; then
    add_result "WARN" "Found $WORLD_WRITABLE world-writable files"
else
    add_result "PASS" "No world-writable files found"
fi

# Check for SUID files
SUID_FILES=$(find / -type f -perm -4000 2>/dev/null | wc -l)
add_result "INFO" "Number of SUID files: $SUID_FILES"

# Check for SGID files
SGID_FILES=$(find / -type f -perm -2000 2>/dev/null | wc -l)
add_result "INFO" "Number of SGID files: $SGID_FILES"

# 6. Log Security
info "=== LOG SECURITY ==="

# Check log file permissions
if [ -d "/var/log/istanbulplus" ]; then
    LOG_PERMS=$(stat -c "%a" /var/log/istanbulplus 2>/dev/null || echo "000")
    if [ "$LOG_PERMS" = "750" ] || [ "$LOG_PERMS" = "640" ]; then
        add_result "PASS" "Log directory has secure permissions"
    else
        add_result "WARN" "Log directory permissions: $LOG_PERMS"
    fi
else
    add_result "WARN" "Istanbul Plus log directory not found"
fi

# Check for log rotation
if [ -f "/etc/logrotate.d/istanbulplus" ]; then
    add_result "PASS" "Log rotation configured"
else
    add_result "WARN" "Log rotation not configured"
fi

# 7. Docker Security
info "=== DOCKER SECURITY ==="

# Check Docker daemon configuration
if [ -f "/etc/docker/daemon.json" ]; then
    add_result "PASS" "Docker daemon configuration exists"
else
    add_result "WARN" "Docker daemon configuration not found"
fi

# Check for running containers
RUNNING_CONTAINERS=$(docker ps -q | wc -l)
add_result "INFO" "Number of running containers: $RUNNING_CONTAINERS"

# Check for privileged containers
PRIVILEGED_CONTAINERS=$(docker ps --format "table {{.Names}}\t{{.Command}}" | grep -c privileged || echo "0")
if [ $PRIVILEGED_CONTAINERS -gt 0 ]; then
    add_result "WARN" "Found $PRIVILEGED_CONTAINERS privileged containers"
else
    add_result "PASS" "No privileged containers found"
fi

# 8. Application Security
info "=== APPLICATION SECURITY ==="

# Check Django settings
if [ -f ".env" ]; then
    if grep -q "DEBUG=True" .env; then
        add_result "FAIL" "Debug mode is enabled in production"
    else
        add_result "PASS" "Debug mode is disabled"
    fi
    
    if grep -q "SECRET_KEY=" .env && ! grep -q "SECRET_KEY=your_" .env; then
        add_result "PASS" "Secret key is configured"
    else
        add_result "FAIL" "Secret key is not properly configured"
    fi
else
    add_result "WARN" "Environment file not found"
fi

# Check SSL certificates
if [ -f "nginx/ssl/istanbulplus.ir.crt" ]; then
    CERT_EXPIRY=$(openssl x509 -enddate -noout -in nginx/ssl/istanbulplus.ir.crt 2>/dev/null | cut -d= -f2)
    if [ -n "$CERT_EXPIRY" ]; then
        add_result "PASS" "SSL certificate found, expires: $CERT_EXPIRY"
    else
        add_result "WARN" "SSL certificate found but cannot read expiry"
    fi
else
    add_result "WARN" "SSL certificate not found"
fi

# 9. Process Security
info "=== PROCESS SECURITY ==="

# Check for suspicious processes
SUSPICIOUS_PROCESSES=$(ps aux | grep -E "(nc|netcat|nmap|masscan)" | grep -v grep | wc -l)
if [ $SUSPICIOUS_PROCESSES -gt 0 ]; then
    add_result "WARN" "Found $SUSPICIOUS_PROCESSES potentially suspicious processes"
else
    add_result "PASS" "No suspicious processes found"
fi

# Check for processes running as root
ROOT_PROCESSES=$(ps aux | awk '$1=="root" {print $11}' | sort | uniq | wc -l)
add_result "INFO" "Number of unique processes running as root: $ROOT_PROCESSES"

# 10. Kernel Security
info "=== KERNEL SECURITY ==="

# Check kernel parameters
if [ "$(cat /proc/sys/net/ipv4/ip_forward)" = "0" ]; then
    add_result "PASS" "IP forwarding is disabled"
else
    add_result "WARN" "IP forwarding is enabled"
fi

if [ "$(cat /proc/sys/net/ipv4/conf/all/send_redirects)" = "0" ]; then
    add_result "PASS" "ICMP redirects are disabled"
else
    add_result "WARN" "ICMP redirects are enabled"
fi

# 11. Package Security
info "=== PACKAGE SECURITY ==="

# Check for security updates
if command -v apt &> /dev/null; then
    SECURITY_UPDATES=$(apt list --upgradable 2>/dev/null | grep -c security || echo "0")
    if [ $SECURITY_UPDATES -gt 0 ]; then
        add_result "WARN" "$SECURITY_UPDATES security updates available"
    else
        add_result "PASS" "No security updates available"
    fi
fi

# Check for installed packages
TOTAL_PACKAGES=$(dpkg -l | wc -l)
add_result "INFO" "Total installed packages: $TOTAL_PACKAGES"

# 12. Summary
info "=== AUDIT SUMMARY ==="
add_result "INFO" "Total issues found: $ISSUES_FOUND"

if [ $ISSUES_FOUND -eq 0 ]; then
    log "Security audit completed successfully - no issues found!"
else
    warn "Security audit completed with $ISSUES_FOUND issues found"
    warn "Please review the results and address the issues"
fi

# Save results
log "Audit results saved to: $AUDIT_RESULTS"

# Display summary
echo ""
echo "=== SECURITY AUDIT SUMMARY ==="
cat $AUDIT_RESULTS | grep -E "\[(FAIL|WARN)\]" | head -10

if [ $ISSUES_FOUND -gt 0 ]; then
    echo ""
    echo "For detailed results, check: $AUDIT_RESULTS"
    exit 1
else
    exit 0
fi
