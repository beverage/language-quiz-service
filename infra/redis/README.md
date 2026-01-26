# Redis Rate Limiting Cache

Redis instances for rate limiting storage in the Language Quiz Service.

## Overview

Redis provides shared, persistent rate limit counters for the API, ensuring consistent rate limiting across service restarts.

**Key Features:**
- ✅ **Flycast networking** - completely private, no public access
- ✅ **Single region deployment** - Amsterdam (ams)
- ✅ **Environment isolation** - separate staging/production instances
- ✅ **Memory-optimized** - LRU eviction, no persistence
- ✅ **Security-hardened** - disabled dangerous commands in production

## Directory Structure

```
redis/
├── staging/
│   ├── fly.toml           # Staging configuration
│   ├── Dockerfile         # Container build
│   ├── redis.conf         # Redis configuration
│   └── start-redis.sh     # Startup script
├── production/
│   ├── fly.toml           # Production configuration  
│   ├── Dockerfile         # Container build
│   ├── redis.conf         # Redis configuration (security hardened)
│   └── start-redis.sh     # Startup script
├── verify-redis-security.sh  # Security verification
└── README.md              # This file
```

## Quick Start

### 1. Create Fly Applications (One-time setup)

```bash
# Staging
cd infra/redis/staging
flyctl launch --no-deploy --name lqs-redis-staging

# Production  
cd infra/redis/production
flyctl launch --no-deploy --name lqs-redis-production
```

### 2. Provision Private IPs (CRITICAL!)

**This step is essential for flycast networking:**

```bash
# Staging - provision private IPv6
flyctl ips allocate-v6 --private -c staging/fly.toml

# Production - provision private IPv6  
flyctl ips allocate-v6 --private -c production/fly.toml
```

⚠️ **Without private IP allocation, flycast networking will not work!**

### 3. Deploy

```bash
# Deploy staging
make redis-deploy ENV=staging

# Deploy production  
make redis-deploy ENV=production
```

### 4. Set Passwords

```bash
# Generate and set secure passwords
make redis-password ENV=staging
make redis-password ENV=production
```

### 5. Configure Application Secrets

Add the Redis connection details to your applications:

```bash
# Staging app
flyctl secrets set \
  REDIS_HOST=lqs-redis-staging.flycast \
  REDIS_PORT=6379 \
  REDIS_PASSWORD='<password-from-step-4>' \
  -a language-quiz-app-staging

# Production app  
flyctl secrets set \
  REDIS_HOST=lqs-redis-production.flycast \
  REDIS_PORT=6379 \
  REDIS_PASSWORD='<password-from-step-4>' \
  -a language-quiz-app-production
```

## Configuration Differences

### Staging vs Production

| Feature | Staging | Production |
|---------|---------|------------|
| **Memory Limit** | 64MB | 64MB |
| **Log Level** | notice | warning |
| **Dangerous Commands** | ✅ Available | ❌ Disabled |
| **CONFIG command** | ✅ Available | ❌ Disabled |
| **FLUSHALL/FLUSHDB** | ✅ Available | ❌ Disabled |

### Security Hardening (Production)

Production Redis disables dangerous commands:
```redis
rename-command FLUSHALL ""
rename-command FLUSHDB ""  
rename-command CONFIG ""
rename-command DEBUG ""
```

## Networking

### Flycast Private Network

Redis instances use **flycast networking** for completely private access:

- ✅ **No public IPs** - instances are not accessible from internet
- ✅ **Private IPv6** - allocated via `fly ips allocate-v6 --private`  
- ✅ **Internal hostnames** - `lqs-redis-{env}.flycast`
- ✅ **Cross-app communication** - apps in same organization can connect

### Connection Format

Applications connect using:
```
Host: lqs-redis-staging.flycast    # or lqs-redis-production.flycast
Port: 6379
Password: <set via secrets>
SSL: false (internal network is secure)
```

## Application Integration

Update your slowapi configuration to use Redis:

```python
from src.core.config import get_settings

settings = get_settings()

# Build Redis URL
redis_url = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}"

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=redis_url,
)
```

## Monitoring & Management

### Using Makefile (from project root)

```bash
# Health check
make redis-health ENV=staging

# View logs
make redis-logs ENV=staging

# Check status
make redis-status ENV=staging

# Memory usage
make redis-memory ENV=staging

# Restart
make redis-restart ENV=staging
```

### Security Verification

```bash
# Verify Redis is not publicly accessible
make redis-security
```

## Troubleshooting

### Connection Failures

1. **Check private IP allocation:**
   ```bash
   flyctl ips list -c staging/fly.toml
   ```
   Should show a private IPv6 address.

2. **Verify flycast deployment:**
   ```bash
   flyctl status -c staging/fly.toml
   ```

3. **Check application secrets:**
   ```bash
   flyctl secrets list -a language-quiz-app-staging
   ```
   Verify REDIS_HOST, REDIS_PORT, REDIS_PASSWORD are set.

### Memory Issues

Rate limiting keys are small, so 64MB should be plenty. If memory issues occur:

1. Check memory usage: `make redis-memory ENV=staging`
2. Clear if needed (staging only): `make redis-clean ENV=staging`

## Security Best Practices

1. ✅ **Private networking only** - no public access
2. ✅ **Password authentication** - random 32-character passwords  
3. ✅ **Dangerous commands disabled** (production)
4. ✅ **Regular security verification** - `make redis-security`
5. ✅ **Minimal surface area** - only port 6379 exposed internally
