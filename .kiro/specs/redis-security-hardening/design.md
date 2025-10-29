# Design Document - Redis Security Hardening

## Overview

این سند طراحی راه‌حل جامع برای رفع آسیب‌پذیری‌های امنیتی Redis و سایر سرویس‌های exposed در دو پروژه Plus و PlusIstanbul را ارائه می‌دهد. بر اساس گزارش BSI آلمان، Redis Server بدون احراز هویت و با bind به 0.0.0.0 در حال اجرا است که یک خطر امنیتی critical محسوب می‌شود.

### Problem Statement

**مشکل اصلی:**
- Redis Server در IP 167.235.140.125 بدون password authentication قابل دسترسی است
- پورت‌های 6379، 6380، 5432، 5433، 5434 به صورت public exposed هستند
- Redis configuration file با bind 0.0.0.0 پیکربندی شده است
- هیچ network isolation بین سرویس‌های داخلی و external وجود ندارد

**تاثیرات امنیتی:**
- دسترسی غیرمجاز به داده‌های cache شده (session data, user info)
- امکان حذف یا تغییر داده‌ها توسط مهاجمان
- دسترسی به اطلاعات حساس مانند credentials
- امکان DoS attack با پر کردن memory
- دسترسی مستقیم به PostgreSQL databases

### Solution Approach

راه‌حل ما شامل 4 لایه امنیتی است:

1. **Authentication Layer**: اضافه کردن password authentication به Redis
2. **Network Layer**: ایزوله کردن شبکه‌های Docker و حذف port exposures
3. **Configuration Layer**: hardening تنظیمات Redis و PostgreSQL
4. **Monitoring Layer**: پیاده‌سازی security monitoring و alerting

## Architecture

### Current Architecture (Vulnerable)

```
Internet
   |
   | (All ports exposed)
   |
   ├─── Port 6379 ──> Redis (no password)
   ├─── Port 6380 ──> Redis (no password)
   ├─── Port 5432 ──> PostgreSQL
   ├─── Port 5433 ──> PostgreSQL
   ├─── Port 5434 ──> PostgreSQL
   ├─── Port 80 ───> Nginx
   └─── Port 443 ──> Nginx
```

### Target Architecture (Secure)

```
Internet
   |
   | (Only 80/443 exposed)
   |
   └─── Nginx (Reverse Proxy)
          |
          ├─── Backend Services (internal network)
          |      |
          |      ├─── Plus Web (8000)
          |      └─── Peykan Backend (8000)
          |
          └─── Frontend Services (internal network)
                 └─── Peykan Frontend (3000)

Internal Docker Networks:
  - plus_internal (isolated)
      ├─── Redis (password protected, no exposed port)
      ├─── PostgreSQL (no exposed port)
      └─── Plus services
  
  - peykan_internal (isolated)
      ├─── Redis (password protected, no exposed port)
      ├─── PostgreSQL (no exposed port)
      └─── Peykan services
  
  - shared_network (for nginx communication only)
      └─── Nginx ←→ Backend/Frontend services
```

### Network Topology

**Plus Project Networks:**
- `istanbulplus_network`: Internal network for Plus services (internal: true)
- `shared_network`: Bridge network for Nginx communication

**PlusIstanbul Project Networks:**
- `peykan_internal`: Internal network for Peykan services (internal: true)
- `peykan_external`: Bridge network for Nginx communication

## Components and Interfaces

### 1. Redis Security Component

#### 1.1 Redis Configuration File
**Location:** `plusistanbul/redis/redis.conf`

**Changes Required:**
```conf
# Network - Bind only to internal Docker network
bind 127.0.0.1 ::1
# Remove: bind 0.0.0.0

# Security - Strong password
requirepass <STRONG_GENERATED_PASSWORD>

# Protected mode
protected-mode yes

# Disable dangerous commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
rename-command SHUTDOWN ""
rename-command KEYS ""
rename-command DEBUG ""

# Connection limits
maxclients 1000
timeout 300

# Memory limits
maxmemory 256mb
maxmemory-policy allkeys-lru

# Logging
logfile /var/log/redis/redis.log
loglevel notice

# Persistence
appendonly yes
appendfsync everysec
```


#### 1.2 Redis Docker Configuration

**Plus Project - docker-compose.yml:**
```yaml
redis:
  image: redis:7-alpine
  container_name: redis
  restart: unless-stopped
  # REMOVE public port exposure
  # ports:
  #   - "6379:6379"
  volumes:
    - plus_redis_data:/data
    - ./redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
    - plus_redis_logs:/var/log/redis
  command: redis-server /usr/local/etc/redis/redis.conf --requirepass ${REDIS_PASSWORD}
  networks:
    - istanbulplus_network  # Internal only
  environment:
    - REDIS_PASSWORD=${REDIS_PASSWORD}
```

**PlusIstanbul Project - docker-compose.production-dev.yml:**
```yaml
redis:
  image: redis:7.4-alpine
  container_name: peykan_redis
  # REMOVE public port exposure
  # ports:
  #   - "6380:6379"
  volumes:
    - peykan_redis_data:/data
    - ./redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
    - peykan_redis_logs:/var/log/redis
  command: redis-server /usr/local/etc/redis/redis.conf --requirepass ${REDIS_PASSWORD}
  networks:
    - peykan_internal  # Internal only
  environment:
    - REDIS_PASSWORD=${REDIS_PASSWORD}
```

#### 1.3 Redis Connection Strings

**Plus Project Environment Variables:**
```bash
REDIS_PASSWORD=<GENERATED_STRONG_PASSWORD>
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/3
REDIS_RATE_LIMIT_URL=redis://:${REDIS_PASSWORD}@redis:6379/4
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/5
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/6
```

**PlusIstanbul Project Environment Variables:**
```bash
REDIS_PASSWORD=<GENERATED_STRONG_PASSWORD>
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/1
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/1
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/1
```

### 2. PostgreSQL Security Component

#### 2.1 PostgreSQL Configuration

**Changes to postgresql.conf:**
```conf
# Network - Listen only on Docker network
listen_addresses = '*'  # OK within Docker internal network
port = 5432

# Connection limits
max_connections = 100

# Security
ssl = off  # Not needed within Docker internal network
password_encryption = scram-sha-256
```

#### 2.2 PostgreSQL Docker Configuration

**Plus Project:**
```yaml
istanbulplus-db:
  image: postgres:15-alpine
  container_name: istanbulplus-db
  # REMOVE public port exposure
  # ports:
  #   - "5433:5432"
  networks:
    - istanbulplus_network  # Internal only
```

**PlusIstanbul Project:**
```yaml
postgres:
  image: postgres:16.3-alpine
  container_name: peykan_postgres
  # REMOVE public port exposure
  # ports:
  #   - "5434:5432"
  networks:
    - peykan_internal  # Internal only
```


### 3. Docker Network Isolation Component

#### 3.1 Network Configuration

**Plus Project Networks:**
```yaml
networks:
  # Internal network - no internet access
  istanbulplus_network:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.20.0.0/16
  
  # Shared network for Nginx communication
  shared_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.21.0.0/16
```

**PlusIstanbul Project Networks:**
```yaml
networks:
  # Internal network - no internet access
  peykan_internal:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.22.0.0/16
  
  # External network for Nginx communication
  peykan_external:
    driver: bridge
    name: plusistanbul_peykan_external
    ipam:
      config:
        - subnet: 172.23.0.0/16
```

#### 3.2 Service Network Assignments

**Plus Project:**
- `istanbulplus-web`: istanbulplus_network + shared_network
- `istanbulplus-db`: istanbulplus_network (internal only)
- `redis`: istanbulplus_network (internal only)
- `istanbulplus-celery`: istanbulplus_network + shared_network
- `nginx`: shared_network + peykan_external

**PlusIstanbul Project:**
- `backend`: peykan_internal + peykan_external
- `frontend`: peykan_internal + peykan_external
- `postgres`: peykan_internal (internal only)
- `redis`: peykan_internal (internal only)
- `celery`: peykan_internal (internal only)

### 4. Environment Variables Security Component

#### 4.1 Password Generation Strategy

**Requirements:**
- Minimum 32 characters
- Mix of uppercase, lowercase, numbers, special characters
- Cryptographically secure random generation
- Different passwords for each service

**Generation Script:**
```bash
#!/bin/bash
# generate-secure-passwords.sh

generate_password() {
    openssl rand -base64 48 | tr -d "=+/" | cut -c1-32
}

echo "REDIS_PASSWORD=$(generate_password)"
echo "POSTGRES_PASSWORD=$(generate_password)"
echo "SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/")"
echo "JWT_SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/")"
```

#### 4.2 Environment File Structure

**Plus Project - .env:**
```bash
# Security - Generated passwords
REDIS_PASSWORD=<GENERATED>
ISTANBULPLUS_DB_PASSWORD=<GENERATED>
ISTANBULPLUS_SECRET_KEY=<GENERATED>

# Redis URLs with password
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/3
REDIS_RATE_LIMIT_URL=redis://:${REDIS_PASSWORD}@redis:6379/4
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/5
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/6
```

**PlusIstanbul Project - backend/.env.production:**
```bash
# Security - Generated passwords
REDIS_PASSWORD=<GENERATED>
POSTGRES_PASSWORD=<GENERATED>
SECRET_KEY=<GENERATED>
JWT_SECRET_KEY=<GENERATED>

# Database URL with password
DATABASE_URL=postgresql://peykan_user:${POSTGRES_PASSWORD}@postgres:5432/peykan

# Redis URLs with password
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/1
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/1
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/1
```


### 5. Security Verification Component

#### 5.1 Verification Script Design

**Script: verify-security.sh**

**Functionality:**
1. Check Redis is not accessible from external network
2. Verify Redis requires password authentication
3. Scan for exposed ports (should only be 80, 443)
4. Test Docker network isolation
5. Verify environment variables are set
6. Check Redis configuration file settings

**Test Cases:**
```bash
# Test 1: Redis external access (should fail)
redis-cli -h 167.235.140.125 -p 6379 PING
# Expected: Connection refused or timeout

# Test 2: Redis password requirement (from inside container)
docker exec peykan_redis redis-cli PING
# Expected: NOAUTH Authentication required

# Test 3: Redis with password (should succeed)
docker exec peykan_redis redis-cli -a ${REDIS_PASSWORD} PING
# Expected: PONG

# Test 4: Port scan
nmap -p 1-65535 167.235.140.125
# Expected: Only 80, 443 open

# Test 5: Network isolation
docker network inspect peykan_internal | grep internal
# Expected: "internal": true
```

#### 5.2 Monitoring Script Design

**Script: monitor-security.sh**

**Functionality:**
1. Continuous monitoring of Redis authentication status
2. Alert on failed authentication attempts
3. Monitor exposed ports
4. Check Docker network configuration
5. Log security events

**Alert Conditions:**
- Redis accessible without password
- Unexpected port exposure detected
- Network isolation disabled
- Failed authentication attempts > threshold
- Configuration file changes detected

### 6. Nginx Configuration Component

#### 6.1 Nginx Security Headers

**nginx.conf additions:**
```nginx
# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

# SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;

# Rate limiting
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
limit_req zone=general burst=20 nodelay;
```

#### 6.2 Backend Proxy Configuration

**For Plus Project:**
```nginx
location / {
    proxy_pass http://istanbulplus-web:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**For PlusIstanbul Project:**
```nginx
location /api/ {
    proxy_pass http://peykan_backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location / {
    proxy_pass http://peykan_frontend:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Data Models

### Security Configuration Model

```yaml
SecurityConfig:
  redis:
    password: string (32+ chars)
    bind_address: "127.0.0.1 ::1"
    protected_mode: true
    max_clients: 1000
    disabled_commands:
      - FLUSHDB
      - FLUSHALL
      - CONFIG
      - SHUTDOWN
      - KEYS
      - DEBUG
  
  postgres:
    password: string (32+ chars)
    listen_addresses: "*"  # OK within internal network
    max_connections: 100
    ssl: false  # Not needed in internal network
  
  docker_networks:
    internal_networks:
      - name: istanbulplus_network
        internal: true
        subnet: 172.20.0.0/16
      - name: peykan_internal
        internal: true
        subnet: 172.22.0.0/16
    
    external_networks:
      - name: shared_network
        internal: false
        subnet: 172.21.0.0/16
      - name: peykan_external
        internal: false
        subnet: 172.23.0.0/16
  
  exposed_ports:
    allowed:
      - 80
      - 443
    blocked:
      - 6379
      - 6380
      - 5432
      - 5433
      - 5434
      - 8000
      - 3000
```


## Error Handling

### 1. Redis Connection Errors

**Scenario:** Application cannot connect to Redis after password is added

**Handling:**
```python
# Django settings
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': os.getenv('REDIS_PASSWORD'),
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'MAX_CONNECTIONS': 50,
        }
    }
}
```

**Error Messages:**
- `NOAUTH Authentication required` → Check REDIS_PASSWORD is set correctly
- `Connection refused` → Check Redis is running and network configuration
- `Timeout` → Check network connectivity and firewall rules

### 2. Docker Network Errors

**Scenario:** Services cannot communicate after network isolation

**Handling:**
- Verify service is connected to correct networks
- Check network exists: `docker network ls`
- Inspect network: `docker network inspect <network_name>`
- Verify DNS resolution: `docker exec <container> ping <service_name>`

**Rollback Procedure:**
```bash
# If services fail to communicate
docker-compose down
# Restore previous docker-compose.yml
docker-compose up -d
```

### 3. Environment Variable Errors

**Scenario:** Missing or incorrect environment variables

**Handling:**
```bash
# Validation script
#!/bin/bash
required_vars=(
    "REDIS_PASSWORD"
    "POSTGRES_PASSWORD"
    "SECRET_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "ERROR: $var is not set"
        exit 1
    fi
done
```

### 4. Port Binding Errors

**Scenario:** Port already in use after removing public exposure

**Handling:**
- Check what's using the port: `sudo lsof -i :6379`
- Stop conflicting service
- Verify Docker port mappings: `docker ps --format "table {{.Names}}\t{{.Ports}}"`

## Testing Strategy

### 1. Unit Tests

**Test Redis Configuration:**
```python
# tests/test_redis_security.py
import redis
import pytest
from django.conf import settings

def test_redis_requires_authentication():
    """Test that Redis requires password"""
    # Try without password - should fail
    with pytest.raises(redis.AuthenticationError):
        r = redis.Redis(host='redis', port=6379, db=0)
        r.ping()
    
    # Try with password - should succeed
    r = redis.Redis(
        host='redis',
        port=6379,
        db=0,
        password=settings.REDIS_PASSWORD
    )
    assert r.ping() == True

def test_redis_dangerous_commands_disabled():
    """Test that dangerous commands are disabled"""
    r = redis.Redis(
        host='redis',
        port=6379,
        db=0,
        password=settings.REDIS_PASSWORD
    )
    
    # These should fail
    with pytest.raises(redis.ResponseError):
        r.execute_command('FLUSHALL')
    
    with pytest.raises(redis.ResponseError):
        r.execute_command('CONFIG', 'GET', '*')
```

### 2. Integration Tests

**Test Network Isolation:**
```bash
#!/bin/bash
# tests/test_network_isolation.sh

echo "Testing network isolation..."

# Test 1: Redis should not be accessible from host
if timeout 2 redis-cli -h localhost -p 6379 PING 2>/dev/null; then
    echo "FAIL: Redis is accessible from host"
    exit 1
fi

# Test 2: Redis should be accessible from backend container
if ! docker exec peykan_backend redis-cli -h redis -a ${REDIS_PASSWORD} PING | grep -q PONG; then
    echo "FAIL: Redis is not accessible from backend"
    exit 1
fi

# Test 3: PostgreSQL should not be accessible from host
if timeout 2 pg_isready -h localhost -p 5432 2>/dev/null; then
    echo "FAIL: PostgreSQL is accessible from host"
    exit 1
fi

echo "PASS: Network isolation working correctly"
```

### 3. Security Tests

**Test Port Exposure:**
```bash
#!/bin/bash
# tests/test_port_exposure.sh

echo "Testing port exposure..."

# Get server IP
SERVER_IP="167.235.140.125"

# Test Redis ports (should be closed)
for port in 6379 6380; do
    if timeout 2 nc -zv $SERVER_IP $port 2>&1 | grep -q succeeded; then
        echo "FAIL: Port $port is exposed"
        exit 1
    fi
done

# Test PostgreSQL ports (should be closed)
for port in 5432 5433 5434; do
    if timeout 2 nc -zv $SERVER_IP $port 2>&1 | grep -q succeeded; then
        echo "FAIL: Port $port is exposed"
        exit 1
    fi
done

# Test HTTP/HTTPS ports (should be open)
for port in 80 443; do
    if ! timeout 2 nc -zv $SERVER_IP $port 2>&1 | grep -q succeeded; then
        echo "FAIL: Port $port is not accessible"
        exit 1
    fi
done

echo "PASS: Port exposure is correct"
```

### 4. Performance Tests

**Test Redis Performance with Authentication:**
```python
# tests/test_redis_performance.py
import time
import redis
from django.conf import settings

def test_redis_performance_with_auth():
    """Ensure authentication doesn't significantly impact performance"""
    r = redis.Redis(
        host='redis',
        port=6379,
        db=0,
        password=settings.REDIS_PASSWORD
    )
    
    # Warm up
    for i in range(100):
        r.set(f'test_key_{i}', f'value_{i}')
    
    # Measure performance
    start = time.time()
    for i in range(1000):
        r.set(f'perf_test_{i}', f'value_{i}')
        r.get(f'perf_test_{i}')
    end = time.time()
    
    duration = end - start
    ops_per_second = 2000 / duration  # 1000 sets + 1000 gets
    
    # Should handle at least 1000 ops/sec
    assert ops_per_second > 1000, f"Performance too low: {ops_per_second} ops/sec"
```


## Deployment Strategy

### Phase 1: Preparation (No Downtime)

**Duration:** 30 minutes

**Steps:**
1. Backup current configurations
2. Generate secure passwords
3. Create updated configuration files
4. Test configurations locally (if possible)
5. Prepare rollback scripts

**Commands:**
```bash
# Backup
mkdir -p ~/backups/security-update-$(date +%Y%m%d)
cp plus/docker-compose.yml ~/backups/security-update-$(date +%Y%m%d)/
cp plusistanbul/docker-compose.production-dev.yml ~/backups/security-update-$(date +%Y%m%d)/
cp plusistanbul/redis/redis.conf ~/backups/security-update-$(date +%Y%m%d)/

# Generate passwords
./scripts/generate-secure-passwords.sh > ~/backups/security-update-$(date +%Y%m%d)/passwords.txt
```

### Phase 2: Plus Project Update (5-10 minutes downtime)

**Duration:** 10 minutes

**Steps:**
1. Update Redis configuration file
2. Update docker-compose.yml
3. Update .env file with passwords
4. Restart services
5. Verify functionality

**Commands:**
```bash
cd ~/plus

# Update configurations (files prepared in Phase 1)
cp ~/security-updates/plus/redis.conf ./redis/redis.conf
cp ~/security-updates/plus/docker-compose.yml ./docker-compose.yml
cp ~/security-updates/plus/.env ./.env

# Restart services
docker-compose down
docker-compose up -d

# Verify
./scripts/verify-plus-security.sh
```

### Phase 3: PlusIstanbul Project Update (5-10 minutes downtime)

**Duration:** 10 minutes

**Steps:**
1. Update Redis configuration file
2. Update docker-compose files
3. Update .env file with passwords
4. Restart services
5. Verify functionality

**Commands:**
```bash
cd ~/plusistanbul

# Update configurations
cp ~/security-updates/plusistanbul/redis.conf ./redis/redis.conf
cp ~/security-updates/plusistanbul/docker-compose.production-dev.yml ./docker-compose.production-dev.yml
cp ~/security-updates/plusistanbul/backend/.env.production ./backend/.env.production

# Restart services
docker-compose -f docker-compose.production-dev.yml down
docker-compose -f docker-compose.production-dev.yml up -d

# Verify
./scripts/verify-peykan-security.sh
```

### Phase 4: Verification and Monitoring (No Downtime)

**Duration:** 15 minutes

**Steps:**
1. Run comprehensive security tests
2. Verify BSI issue is resolved
3. Test application functionality
4. Enable monitoring
5. Document changes

**Commands:**
```bash
# Security verification
./scripts/verify-security-complete.sh

# Test from external network
redis-cli -h 167.235.140.125 -p 6379 PING
# Should fail with connection refused

# Port scan
nmap -p 1-65535 167.235.140.125
# Should only show 80, 443

# Application tests
curl -I https://istanbulplus.ir
curl -I https://peykantravelistanbul.com
```

### Rollback Procedure

**If issues occur during deployment:**

```bash
# Rollback Plus Project
cd ~/plus
docker-compose down
cp ~/backups/security-update-$(date +%Y%m%d)/docker-compose.yml ./
docker-compose up -d

# Rollback PlusIstanbul Project
cd ~/plusistanbul
docker-compose -f docker-compose.production-dev.yml down
cp ~/backups/security-update-$(date +%Y%m%d)/docker-compose.production-dev.yml ./
docker-compose -f docker-compose.production-dev.yml up -d
```

## Security Checklist

### Pre-Deployment Checklist

- [ ] Backup all configuration files
- [ ] Generate strong passwords (32+ characters)
- [ ] Test Redis configuration syntax
- [ ] Test Docker Compose configuration syntax
- [ ] Prepare rollback scripts
- [ ] Schedule maintenance window
- [ ] Notify users of brief downtime

### Post-Deployment Checklist

- [ ] Redis requires password authentication
- [ ] Redis not accessible from external network
- [ ] PostgreSQL not accessible from external network
- [ ] Only ports 80 and 443 exposed publicly
- [ ] Docker networks properly isolated
- [ ] All services can communicate internally
- [ ] Application functionality verified
- [ ] Monitoring enabled
- [ ] Documentation updated
- [ ] BSI issue resolved (verify after 24 hours)

## Monitoring and Alerting

### Metrics to Monitor

1. **Redis Metrics:**
   - Authentication failures
   - Connection attempts
   - Memory usage
   - Command execution rate
   - Slow queries

2. **Network Metrics:**
   - Exposed ports
   - Network isolation status
   - Connection attempts to internal services

3. **Application Metrics:**
   - Cache hit rate
   - Response times
   - Error rates
   - Session management

### Alert Rules

```yaml
alerts:
  - name: redis_no_auth
    condition: redis_auth_required == false
    severity: critical
    action: immediate_notification
  
  - name: redis_exposed
    condition: redis_port_exposed == true
    severity: critical
    action: immediate_notification
  
  - name: postgres_exposed
    condition: postgres_port_exposed == true
    severity: critical
    action: immediate_notification
  
  - name: auth_failures
    condition: redis_auth_failures > 10 in 5m
    severity: warning
    action: log_and_notify
  
  - name: network_isolation_disabled
    condition: internal_network_isolated == false
    severity: critical
    action: immediate_notification
```

### Monitoring Script

```bash
#!/bin/bash
# scripts/monitor-security.sh

while true; do
    # Check Redis authentication
    if docker exec peykan_redis redis-cli PING 2>&1 | grep -q PONG; then
        echo "ALERT: Redis accessible without password!"
        # Send alert
    fi
    
    # Check port exposure
    for port in 6379 6380 5432 5433 5434; do
        if timeout 2 nc -zv localhost $port 2>&1 | grep -q succeeded; then
            echo "ALERT: Port $port is exposed!"
            # Send alert
        fi
    done
    
    # Check network isolation
    if ! docker network inspect peykan_internal | grep -q '"internal": true'; then
        echo "ALERT: Network isolation disabled!"
        # Send alert
    fi
    
    sleep 300  # Check every 5 minutes
done
```

## Documentation

### User Documentation (Persian)

راهنمای کامل deployment در فایل جداگانه `DEPLOYMENT_GUIDE_FA.md` ارائه خواهد شد که شامل:

1. مقدمه و توضیح مشکل امنیتی
2. مراحل آماده‌سازی
3. دستورات deployment گام به گام
4. نحوه تست و تایید
5. عیب‌یابی مشکلات رایج
6. روش rollback در صورت بروز مشکل

### Technical Documentation

مستندات فنی شامل:
- معماری امنیتی جدید
- تنظیمات Redis و PostgreSQL
- پیکربندی Docker networks
- راهنمای monitoring
- API changes (if any)

## Performance Considerations

### Redis Performance Impact

**Authentication Overhead:**
- Password authentication adds ~0.1ms per connection
- Negligible impact on overall performance
- Connection pooling minimizes authentication frequency

**Network Isolation Impact:**
- Internal Docker networks have minimal latency
- No performance degradation expected
- May actually improve performance by reducing external noise

### Optimization Strategies

1. **Connection Pooling:**
```python
CACHES = {
    'default': {
        'OPTIONS': {
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        }
    }
}
```

2. **Redis Pipelining:**
```python
pipe = redis_client.pipeline()
for key, value in data.items():
    pipe.set(key, value)
pipe.execute()
```

3. **Persistent Connections:**
```python
CACHES = {
    'default': {
        'OPTIONS': {
            'SOCKET_KEEPALIVE': True,
            'SOCKET_KEEPALIVE_OPTIONS': {
                socket.TCP_KEEPIDLE: 1,
                socket.TCP_KEEPINTVL: 1,
                socket.TCP_KEEPCNT: 5,
            }
        }
    }
}
```

## Conclusion

این طراحی یک راه‌حل جامع و چند لایه برای رفع آسیب‌پذیری‌های امنیتی ارائه می‌دهد:

1. **Authentication Layer**: Redis با password محافظت می‌شود
2. **Network Layer**: شبکه‌های Docker ایزوله می‌شوند
3. **Configuration Layer**: تنظیمات امنیتی hardening می‌شوند
4. **Monitoring Layer**: نظارت مستمر بر امنیت

با اجرای این طراحی:
- مشکل گزارش شده توسط BSI برطرف می‌شود
- امنیت کلی سیستم بهبود می‌یابد
- تاثیر بر performance minimal است
- قابلیت rollback وجود دارد
- monitoring و alerting فعال می‌شود
