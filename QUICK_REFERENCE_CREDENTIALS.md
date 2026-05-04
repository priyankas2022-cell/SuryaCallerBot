# 🎯 QUICK REFERENCE - Database Credentials

## 📊 CURRENT CREDENTIALS (AS FOUND IN CODE)

### PostgreSQL Database
```
Username: postgres
Password: postgres
Database: postgres
Host: localhost:5432
Connection String: postgresql+asyncpg://postgres:postgres@localhost:5432/postgres
```

### Redis Cache
```
Password: redissecret
Host: localhost:6379
Connection String: redis://:redissecret@localhost:6379
```

### MinIO Object Storage
```
Access Key: minioadmin
Secret Key: minioadmin
Endpoint: localhost:9000
Bucket: voice-audio
```

---

## 📁 FILES CONTAINING CREDENTIALS

1. **`api/.env`** - Local development configuration
2. **`docker-compose.yaml`** - Production Docker deployment
3. **`docker-compose-local.yaml`** - Local Docker deployment

---

## 🔧 HOW TO UPDATE CREDENTIALS

### Option 1: Use Automated Script (RECOMMENDED)

```powershell
cd d:\dograh-main\dograh-main
.\update_database_credentials.ps1
```

The script will:
- Ask for new credentials interactively
- Backup all existing files
- Update all configuration files automatically
- Provide next steps

### Option 2: Manual Update

#### Step 1: Edit `api\.env`
```env
DATABASE_URL="postgresql+asyncpg://NEW_USER:NEW_PASSWORD@localhost:5432/NEW_DATABASE"
REDIS_URL="redis://:NEW_REDIS_PASSWORD@localhost:6379"
MINIO_ACCESS_KEY=NEW_ACCESS_KEY
MINIO_SECRET_KEY=NEW_SECRET_KEY
```

#### Step 2: Edit `docker-compose-local.yaml`
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

#### Step 3: Edit `docker-compose.yaml`
Update the same values in both the service definitions AND the api service environment variables.

---

## ⚡ APPLY CHANGES

After updating credentials:

```powershell
# 1. Stop containers
docker compose down

# 2. Remove old volumes (DELETES DATA!)
docker volume rm dograh-main_postgres_data
docker volume rm dograh-main_redis_data
docker volume rm dograh-main_minio_data

# 3. Start with new credentials
docker compose up -d

# 4. Restart backend
# (Stop and restart your Python/backend process)
```

---

## 🔐 RECOMMENDED STRONG PASSWORDS

Generate secure passwords using Python:

```python
import secrets
import string

alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
password = ''.join(secrets.choice(alphabet) for _ in range(32))
print(f"Secure password: {password}")
```

Example strong passwords:
- PostgreSQL: `Pr0st_P@ssw0rd_S3cur3_2024!`
- Redis: `R3d1s_C@ch3_K3y_Sup3r_S3cr3t!`
- MinIO: `M1n10_St0r@ge_S3cur3_Acc3ss!`

---

## 📋 VERIFICATION CHECKLIST

After updating:

- [ ] Backend starts without errors
- [ ] Can connect to database
- [ ] Redis connection works
- [ ] MinIO storage accessible
- [ ] Frontend loads properly
- [ ] API endpoints respond
- [ ] Workflows can be created
- [ ] No authentication errors

Test database connection:
```powershell
# Test PostgreSQL
docker exec -it dograh-main-postgres-1 psql -U postgres -c "SELECT 1;"

# Test Redis
docker exec -it dograh-main-redis-1 redis-cli -a NEW_PASSWORD ping

# Test MinIO
curl http://localhost:9000/minio/health/live
```

---

## 🚨 TROUBLESHOOTING

### Backend won't start after update
- Check connection string format in `api/.env`
- Verify Docker containers are running
- Check logs: `docker compose logs api`

### Special characters in password
URL-encode special characters:
- `@` → `%40`
- `:` → `%3A`
- `/` → `%2F`

Example: `P@ssword` becomes `P%40ssword`

### Can't connect to database
1. Verify container is running: `docker ps`
2. Check port is accessible: `netstat -ano | findstr 5432`
3. Test with: `docker exec -it postgres_container psql -U postgres`

---

## 📄 FILES CREATED FOR YOU

1. **`DATABASE_CREDENTIALS_GUIDE.md`** - Complete detailed guide
2. **`update_database_credentials.ps1`** - Automated update script
3. **`QUICK_REFERENCE_CREDENTIALS.md`** - This quick reference

---

## 🎯 RECOMMENDED NEXT ACTION

### Right Now:

1. **Run the update script**:
   ```powershell
   .\update_database_credentials.ps1
   ```

2. **Follow the prompts** to enter new credentials

3. **Apply changes** using the commands provided

4. **Test everything works**

### Keep Safe:
- Store new credentials in a password manager
- Keep backup files secure
- Update team documentation
- Rotate credentials every 90 days

---

**Need more details? See `DATABASE_CREDENTIALS_GUIDE.md` for complete information!** 📚
