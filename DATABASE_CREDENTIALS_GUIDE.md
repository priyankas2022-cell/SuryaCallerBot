# 🗄️ Database Configuration Analysis - SuryaCaller

## 📊 CURRENT DATABASE CREDENTIALS FOUND

### 1. PostgreSQL Database (Main Application Database)

**Location**: Multiple files analyzed

#### Current Credentials:

| Parameter | Value | Location |
|-----------|-------|----------|
| **Username** | `postgres` | docker-compose.yaml, .env |
| **Password** | `postgres` | docker-compose.yaml, .env |
| **Database Name** | `postgres` | docker-compose.yaml, .env |
| **Host** | `localhost` (local) / `postgres` (docker) | .env, docker-compose.yaml |
| **Port** | `5432` | Standard PostgreSQL port |
| **Image** | `pgvector/pgvector:pg17` | PostgreSQL 17 with vector support |

#### Connection Strings:

**Local Development (api/.env)**:
```
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
```

**Docker Compose (docker-compose.yaml)**:
```
DATABASE_URL: "postgresql+asyncpg://postgres:postgres@postgres:5432/postgres"
```

---

### 2. Redis (Cache & Message Broker)

#### Current Credentials:

| Parameter | Value | Location |
|-----------|-------|----------|
| **Password** | `redissecret` | docker-compose.yaml, .env |
| **Host** | `localhost` (local) / `redis` (docker) | .env, docker-compose.yaml |
| **Port** | `6379` | Standard Redis port |
| **Image** | `redis:7` | Redis version 7 |

#### Connection Strings:

**Local Development (api/.env)**:
```
REDIS_URL="redis://:redissecret@localhost:6379"
```

**Docker Compose (docker-compose.yaml)**:
```
REDIS_URL: "redis://:redissecret@redis:6379"
```

---

### 3. MinIO (Object Storage - S3 Compatible)

#### Current Credentials:

| Parameter | Value | Location |
|-----------|-------|----------|
| **Access Key** | `minioadmin` | docker-compose.yaml, .env |
| **Secret Key** | `minioadmin` | docker-compose.yaml, .env |
| **Endpoint** | `localhost:9000` (local) / `minio:9000` (docker) | .env, docker-compose.yaml |
| **Console Port** | `9001` | MinIO web console |
| **Bucket** | `voice-audio` | .env |
| **Image** | `minio/minio` | Latest MinIO |

---

## 🔐 SECURITY ASSESSMENT

### ⚠️ CURRENT ISSUES:

1. **Default Passwords**: Using default/weak passwords
   - PostgreSQL: `postgres` / `postgres`
   - MinIO: `minioadmin` / `minioadmin`
   - Redis: `redissecret`

2. **Exposed in Code**: Credentials stored in plain text files
   - `api/.env` - Contains all credentials
   - `docker-compose.yaml` - Contains database credentials
   - `docker-compose-local.yaml` - Contains database credentials

3. **No Encryption**: Passwords not encrypted at rest

### ✅ RECOMMENDATIONS:

1. Use strong, randomly generated passwords
2. Move sensitive credentials to environment variables or secret management
3. Use `.gitignore` to prevent committing `.env` files
4. Consider using Docker secrets or Kubernetes secrets in production

---

## 🛠️ HOW TO UPDATE DATABASE CREDENTIALS

### Step-by-Step Guide:

#### 1. Choose New Credentials

**PostgreSQL**:
- Username: Keep as `postgres` (or change to custom)
- Password: Generate strong password (e.g., `MyStr0ngP@ssw0rd!2024`)
- Database: Keep as `postgres` (or create new)

**Redis**:
- Password: Generate strong password (e.g., `R3d1sS3cur3P@ss!`)

**MinIO**:
- Access Key: Generate random string (e.g., `myaccesskey2024`)
- Secret Key: Generate strong password (e.g., `MySup3rS3cr3tK3y!`)

#### 2. Update Files

You need to update these files:

**File 1: `api/.env`** (Local development)
```env
# Database Configuration
DATABASE_URL="postgresql+asyncpg://NEW_USER:NEW_PASSWORD@localhost:5432/NEW_DATABASE"
REDIS_URL="redis://:NEW_REDIS_PASSWORD@localhost:6379"

# MinIO Configuration
MINIO_ACCESS_KEY=NEW_ACCESS_KEY
MINIO_SECRET_KEY=NEW_SECRET_KEY
```

**File 2: `docker-compose.yaml`** (Docker deployment)
```yaml
services:
  postgres:
    environment:
      POSTGRES_USER: NEW_USER
      POSTGRES_PASSWORD: NEW_PASSWORD
      POSTGRES_DB: NEW_DATABASE
  
  redis:
    command: --requirepass NEW_REDIS_PASSWORD
  
  minio:
    environment:
      MINIO_ROOT_USER: NEW_ACCESS_KEY
      MINIO_ROOT_PASSWORD: NEW_SECRET_KEY
  
  api:
    environment:
      DATABASE_URL: "postgresql+asyncpg://NEW_USER:NEW_PASSWORD@postgres:5432/NEW_DATABASE"
      REDIS_URL: "redis://:NEW_REDIS_PASSWORD@redis:6379"
      MINIO_ACCESS_KEY: NEW_ACCESS_KEY
      MINIO_SECRET_KEY: NEW_SECRET_KEY
```

**File 3: `docker-compose-local.yaml`** (Local Docker deployment)
```yaml
services:
  postgres:
    environment:
      POSTGRES_USER: NEW_USER
      POSTGRES_PASSWORD: NEW_PASSWORD
      POSTGRES_DB: NEW_DATABASE
  
  redis:
    command: --requirepass NEW_REDIS_PASSWORD
  
  minio:
    environment:
      MINIO_ROOT_USER: NEW_ACCESS_KEY
      MINIO_ROOT_PASSWORD: NEW_SECRET_KEY
```

#### 3. Apply Changes

After updating credentials, you MUST:

1. **Stop all containers**:
   ```powershell
   docker compose down
   ```

2. **Remove old volumes** (WARNING: This deletes all data!):
   ```powershell
   docker volume rm dograh-main_postgres_data
   docker volume rm dograh-main_redis_data
   docker volume rm dograh-main_minio_data
   ```

3. **Start services again**:
   ```powershell
   docker compose up -d
   ```

4. **Update application .env**:
   Edit `api\.env` with new credentials

5. **Restart backend**:
   ```powershell
   # Stop current backend
   # Restart with new credentials
   ```

---

## 📝 COMPLETE CREDENTIAL MAPPING

### All Files That Need Updating:

| File Name | Credentials Stored | Purpose |
|-----------|-------------------|---------|
| **`api/.env`** | DATABASE_URL, REDIS_URL, MINIO keys | Local development |
| **`docker-compose.yaml`** | POSTGRES_*, REDIS_*, MINIO_* | Production Docker |
| **`docker-compose-local.yaml`** | POSTGRES_*, REDIS_*, MINIO_* | Local Docker |
| **`api/db/database.py`** | Reads from DATABASE_URL | Database connection code |

---

## 🔍 CODE ANALYSIS

### Database Connection Code:

**File**: `api/db/database.py`

The application uses SQLAlchemy with asyncpg driver:

```python
from sqlalchemy.ext.asyncio import create_async_engine
from urllib.parse import urlparse

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(
    DATABASE_URL.replace("+asyncpg", "+psycopg2"),  # For migrations
    echo=False,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
)
```

### How It Works:

1. Reads `DATABASE_URL` from environment variable
2. Parses connection string to extract:
   - Username
   - Password
   - Host
   - Port
   - Database name
3. Creates connection pool
4. Manages connections automatically

---

## 🎯 RECOMMENDED NEW CREDENTIALS

### Strong Password Examples:

**PostgreSQL**:
```
Username: postgres
Password: Pr0stGr3s_P@ssw0rd_2024_Secure!
Database: postgres
```

**Redis**:
```
Password: R3d1s_C@ch3_S3cur3_K3y_2024!
```

**MinIO**:
```
Access Key: minio_access_2024_secure
Secret Key: M1n10_Sup3r_S3cr3t_K3y_2024!
```

### Generate Your Own:

Use Python to generate secure passwords:
```python
import secrets
import string

# Generate 32-character password
alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
password = ''.join(secrets.choice(alphabet) for _ in range(32))
print(f"Generated password: {password}")
```

---

## ⚡ QUICK UPDATE SCRIPT

### PowerShell Script to Update Credentials:

```powershell
# Define new credentials
$NEW_DB_PASSWORD = "YourNewStrongPassword123!"
$NEW_REDIS_PASSWORD = "YourRedisPassword456!"
$NEW_MINIO_ACCESS = "yourminioaccesskey"
$NEW_MINIO_SECRET = "YourMinioSecret789!"

# Update api/.env
$envContent = Get-Content "api\.env" -Raw
$envContent = $envContent -replace 'postgres:postgres', "postgres:$NEW_DB_PASSWORD"
$envContent = $envContent -replace ':redissecret@', ":$NEW_REDIS_PASSWORD@"
$envContent = $envContent -replace 'MINIO_ACCESS_KEY=minioadmin', "MINIO_ACCESS_KEY=$NEW_MINIO_ACCESS"
$envContent = $envContent -replace 'MINIO_SECRET_KEY=minioadmin', "MINIO_SECRET_KEY=$NEW_MINIO_SECRET"
$envContent | Set-Content "api\.env"

Write-Host "✅ Credentials updated in api\.env"

# Note: You'll also need to update docker-compose files manually
Write-Host "⚠️ Remember to update docker-compose.yaml and docker-compose-local.yaml manually"
```

---

## 📋 MIGRATION CHECKLIST

When changing database credentials:

### Before Changing:
- [ ] Backup existing database (if data needs to be preserved)
- [ ] Document current credentials
- [ ] Notify team members
- [ ] Schedule downtime if production

### During Change:
- [ ] Stop all application instances
- [ ] Stop Docker containers
- [ ] Update credentials in all files
- [ ] Remove old volumes (if acceptable)
- [ ] Start Docker services
- [ ] Verify services are running

### After Change:
- [ ] Test database connection
- [ ] Run database migrations
- [ ] Test application functionality
- [ ] Monitor logs for errors
- [ ] Update documentation

---

## 🚨 IMPORTANT WARNINGS

### ⚠️ Data Loss Warning:

Changing database credentials and removing volumes will:
- **DELETE all existing data**
- Remove all users, workflows, configurations
- Reset the entire application state

**To preserve data**:
1. Export data before changes (pg_dump)
2. Import data after credential changes
3. Or don't remove volumes (keep old credentials)

### ⚠️ Application Downtime:

During credential update:
- Backend will be unavailable
- Frontend won't work
- Active sessions will be lost
- Scheduled tasks will fail

**Plan accordingly!**

---

## 🔧 TROUBLESHOOTING

### Issue: Can't Connect After Update

**Symptoms**: Backend shows connection errors

**Solutions**:
1. Check connection string format
2. Verify username/password are correct
3. Ensure no special characters need URL encoding
4. Check Docker container is running
5. Verify port is accessible

### Issue: Special Characters in Password

If your password contains special characters (`@`, `:`, `/`, etc.), you must URL-encode them:

```
@ → %40
: → %3A
/ → %2F
? → %3F
= → %3D
```

Example:
```
Bad: postgres://user:P@ssword@localhost:5432/db
Good: postgres://user:P%40ssword@localhost:5432/db
```

### Issue: Docker Containers Won't Start

**Check**:
1. YAML syntax is correct (indentation matters!)
2. No trailing spaces in environment variables
3. Quotes around values if needed
4. Container names don't conflict

---

## 📊 SUMMARY TABLE

### Current vs Recommended Configuration:

| Service | Current | Recommended | Priority |
|---------|---------|-------------|----------|
| **PostgreSQL User** | `postgres` | `postgres` or custom | Low |
| **PostgreSQL Password** | `postgres` ❌ | Strong password (32+ chars) | **CRITICAL** |
| **Redis Password** | `redissecret` ❌ | Strong random password | **HIGH** |
| **MinIO Access Key** | `minioadmin` ❌ | Random string | **HIGH** |
| **MinIO Secret Key** | `minioadmin` ❌ | Strong password | **CRITICAL** |

---

## 🎯 NEXT STEPS

### Immediate Actions:

1. **Choose new credentials**
   - Use strong, unique passwords
   - Store securely (password manager)

2. **Update configuration files**
   - `api/.env`
   - `docker-compose.yaml`
   - `docker-compose-local.yaml`

3. **Apply changes**
   - Stop services
   - Update credentials
   - Restart services

4. **Verify everything works**
   - Test backend API
   - Test frontend UI
   - Check database connectivity

### Optional Enhancements:

1. **Use environment variables** instead of hardcoded values
2. **Implement secret management** (HashiCorp Vault, AWS Secrets Manager)
3. **Enable SSL/TLS** for database connections
4. **Set up monitoring** for database access
5. **Rotate credentials regularly** (every 90 days)

---

**Ready to update your credentials? Follow the step-by-step guide above!** 🔐
