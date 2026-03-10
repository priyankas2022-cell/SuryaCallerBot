# SuryaCaller - Update Database Credentials Script
# This script helps you update all database credentials safely

Write-Host "`n🔐 DATABASE CREDENTIALS UPDATE UTILITY" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Gray

# Step 1: Get new credentials from user
Write-Host "`n📋 STEP 1: Enter New Credentials" -ForegroundColor Yellow
Write-Host "Choose strong, secure passwords for your services" -ForegroundColor Gray

Write-Host "`n--- PostgreSQL Database ---" -ForegroundColor Cyan
$DB_USER = Read-Host "  Database Username [postgres]"
if ([string]::IsNullOrWhiteSpace($DB_USER)) { $DB_USER = "postgres" }

$DB_PASSWORD = Read-Host "  Database Password (choose a strong password)"
$DB_NAME = Read-Host "  Database Name [postgres]"
if ([string]::IsNullOrWhiteSpace($DB_NAME)) { $DB_NAME = "postgres" }

Write-Host "`n--- Redis Cache ---" -ForegroundColor Cyan
$REDIS_PASSWORD = Read-Host "  Redis Password (choose a strong password)"

Write-Host "`n--- MinIO Object Storage ---" -ForegroundColor Cyan
$MINIO_ACCESS = Read-Host "  MinIO Access Key"
$MINIO_SECRET = Read-Host "  MinIO Secret Key (choose a strong password)"

# Validate inputs
if ([string]::IsNullOrWhiteSpace($DB_PASSWORD)) {
    Write-Host "`n❌ ERROR: Database password cannot be empty!" -ForegroundColor Red
    exit 1
}

if ([string]::IsNullOrWhiteSpace($REDIS_PASSWORD)) {
    Write-Host "`n❌ ERROR: Redis password cannot be empty!" -ForegroundColor Red
    exit 1
}

# Display summary
Write-Host "`n📊 STEP 2: Configuration Summary" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Gray
Write-Host "`nPostgreSQL:" -ForegroundColor Cyan
Write-Host "  Username: $DB_USER" -ForegroundColor White
Write-Host "  Password: $('*' * $DB_PASSWORD.Length)" -ForegroundColor White
Write-Host "  Database: $DB_NAME" -ForegroundColor White
Write-Host "  Host: localhost:5432" -ForegroundColor Gray

Write-Host "`nRedis:" -ForegroundColor Cyan
Write-Host "  Password: $('*' * $REDIS_PASSWORD.Length)" -ForegroundColor White
Write-Host "  Port: 6379" -ForegroundColor Gray

Write-Host "`nMinIO:" -ForegroundColor Cyan
Write-Host "  Access Key: $MINIO_ACCESS" -ForegroundColor White
Write-Host "  Secret Key: $('*' * $MINIO_SECRET.Length)" -ForegroundColor White
Write-Host "  Endpoint: localhost:9000" -ForegroundColor Gray

Write-Host "`n⚠️ IMPORTANT:" -ForegroundColor Yellow
Write-Host "This will update the following files:" -ForegroundColor White
Write-Host "  • api\.env" -ForegroundColor Gray
Write-Host "  • docker-compose.yaml" -ForegroundColor Gray
Write-Host "  • docker-compose-local.yaml" -ForegroundColor Gray
Write-Host "`n⚠️ WARNING: Changing credentials will require restarting all services!" -ForegroundColor Red

$confirm = Read-Host "`nDo you want to proceed? (y/n)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "`n❌ Operation cancelled by user" -ForegroundColor Red
    exit 0
}

# Step 3: Backup existing files
Write-Host "`n📦 STEP 3: Creating Backups..." -ForegroundColor Yellow

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "credential_backups_$timestamp"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# Backup files
$filesToBackup = @(
    "api\.env",
    "docker-compose.yaml",
    "docker-compose-local.yaml"
)

foreach ($file in $filesToBackup) {
    if (Test-Path $file) {
        Copy-Item $file "$backupDir\$file.bak" -Force
        Write-Host "  ✓ Backed up: $file" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ Not found: $file" -ForegroundColor Yellow
    }
}

Write-Host "`nBackups saved to: .\$backupDir" -ForegroundColor Green

# Step 4: Update api\.env
Write-Host "`n🔧 STEP 4: Updating api\.env..." -ForegroundColor Yellow

try {
    $envContent = Get-Content "api\.env" -Raw
    
    # Build new DATABASE_URL
    $newDbUrl = "postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}"
    
    # Replace DATABASE_URL
    $envContent = $envContent -replace 'DATABASE_URL="[^"]*"', "DATABASE_URL=`"$newDbUrl`""
    
    # Replace REDIS_URL
    $newRedisUrl = "redis://:${REDIS_PASSWORD}@localhost:6379"
    $envContent = $envContent -replace 'REDIS_URL="[^"]*"', "REDIS_URL=`"$newRedisUrl`""
    
    # Replace MINIO_ACCESS_KEY
    $envContent = $envContent -replace 'MINIO_ACCESS_KEY=[^\r\n]*', "MINIO_ACCESS_KEY=$MINIO_ACCESS"
    
    # Replace MINIO_SECRET_KEY
    $envContent = $envContent -replace 'MINIO_SECRET_KEY=[^\r\n]*', "MINIO_SECRET_KEY=$MINIO_SECRET"
    
    # Save updated file
    $envContent | Set-Content "api\.env" -NoNewline
    Write-Host "  ✓ api\.env updated successfully" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Error updating api\.env: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 5: Update docker-compose-local.yaml
Write-Host "`n🔧 STEP 5: Updating docker-compose-local.yaml..." -ForegroundColor Yellow

try {
    $composeLocalContent = Get-Content "docker-compose-local.yaml" -Raw
    
    # Replace PostgreSQL credentials
    $composeLocalContent = $composeLocalContent -replace 'POSTGRES_USER: \w+', "POSTGRES_USER: $DB_USER"
    $composeLocalContent = $composeLocalContent -replace 'POSTGRES_PASSWORD: \w+', "POSTGRES_PASSWORD: $DB_PASSWORD"
    $composeLocalContent = $composeLocalContent -replace 'POSTGRES_DB: \w+', "POSTGRES_DB: $DB_NAME"
    
    # Replace Redis password
    $composeLocalContent = $composeLocalContent -replace '--requirepass \w+', "--requirepass $REDIS_PASSWORD"
    $composeLocalContent = $composeLocalContent -replace '-a \w+ ping', "-a $REDIS_PASSWORD ping"
    
    # Replace MinIO credentials
    $composeLocalContent = $composeLocalContent -replace 'MINIO_ROOT_USER: \w+', "MINIO_ROOT_USER: $MINIO_ACCESS"
    $composeLocalContent = $composeLocalContent -replace 'MINIO_ROOT_PASSWORD: \w+', "MINIO_ROOT_PASSWORD: $MINIO_SECRET"
    
    # Save updated file
    $composeLocalContent | Set-Content "docker-compose-local.yaml" -NoNewline
    Write-Host "  ✓ docker-compose-local.yaml updated successfully" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Error updating docker-compose-local.yaml: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 6: Update docker-compose.yaml
Write-Host "`n🔧 STEP 6: Updating docker-compose.yaml..." -ForegroundColor Yellow

try {
    $composeContent = Get-Content "docker-compose.yaml" -Raw
    
    # Replace PostgreSQL credentials in postgres service
    $composeContent = $composeContent -replace 'POSTGRES_USER: \w+', "POSTGRES_USER: $DB_USER"
    $composeContent = $composeContent -replace 'POSTGRES_PASSWORD: \w+', "POSTGRES_PASSWORD: $DB_PASSWORD"
    $composeContent = $composeContent -replace 'POSTGRES_DB: \w+', "POSTGRES_DB: $DB_NAME"
    
    # Replace Redis password in redis service
    $composeContent = $composeContent -replace '--requirepass \w+', "--requirepass $REDIS_PASSWORD"
    $composeContent = $composeContent -replace '-a \w+ ping', "-a $REDIS_PASSWORD ping"
    
    # Replace MinIO credentials in minio service
    $composeContent = $composeContent -replace 'MINIO_ROOT_USER: \w+', "MINIO_ROOT_USER: $MINIO_ACCESS"
    $composeContent = $composeContent -replace 'MINIO_ROOT_PASSWORD: \w+', "MINIO_ROOT_PASSWORD: $MINIO_SECRET"
    
    # Replace DATABASE_URL in api service
    $newDbUrlDocker = "postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}"
    $composeContent = $composeContent -replace 'DATABASE_URL: "[^"]*"', "DATABASE_URL: `"$newDbUrlDocker`""
    
    # Replace REDIS_URL in api service
    $newRedisUrlDocker = "redis://:${REDIS_PASSWORD}@redis:6379"
    $composeContent = $composeContent -replace 'REDIS_URL: "[^"]*"', "REDIS_URL: `"$newRedisUrlDocker`""
    
    # Replace MinIO environment variables in api service
    $composeContent = $composeContent -replace 'MINIO_ACCESS_KEY: \w+', "MINIO_ACCESS_KEY: $MINIO_ACCESS"
    $composeContent = $composeContent -replace 'MINIO_SECRET_KEY: \w+', "MINIO_SECRET_KEY: $MINIO_SECRET"
    
    # Save updated file
    $composeContent | Set-Content "docker-compose.yaml" -NoNewline
    Write-Host "  ✓ docker-compose.yaml updated successfully" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Error updating docker-compose.yaml: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 7: Instructions for applying changes
Write-Host "`n✅ STEP 7: Apply Changes" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Gray

Write-Host "`n🎉 CREDENTIALS UPDATED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "`nUpdated Files:" -ForegroundColor Cyan
Write-Host "  ✓ api\.env" -ForegroundColor Green
Write-Host "  ✓ docker-compose.yaml" -ForegroundColor Green
Write-Host "  ✓ docker-compose-local.yaml" -ForegroundColor Green
Write-Host "`nBackups Created:" -ForegroundColor Cyan
Write-Host "  ✓ $backupDir\*.bak" -ForegroundColor Green

Write-Host "`n⚠️ NEXT STEPS REQUIRED:" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Yellow
Write-Host "`nTo apply the new credentials, you MUST:" -ForegroundColor White
Write-Host "`n1. Stop all running containers:" -ForegroundColor Cyan
Write-Host "   docker compose down" -ForegroundColor Gray

Write-Host "`n2. Remove old volumes (WARNING: This deletes existing data!):" -ForegroundColor Cyan
Write-Host "   docker volume rm dograh-main_postgres_data" -ForegroundColor Gray
Write-Host "   docker volume rm dograh-main_redis_data" -ForegroundColor Gray
Write-Host "   docker volume rm dograh-main_minio_data" -ForegroundColor Gray

Write-Host "`n3. Start services with new credentials:" -ForegroundColor Cyan
Write-Host "   docker compose up -d" -ForegroundColor Gray

Write-Host "`n4. Restart the backend application" -ForegroundColor Cyan

Write-Host "`n📝 IMPORTANT NOTES:" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Yellow
Write-Host "• All existing data will be lost when volumes are removed" -ForegroundColor White
Write-Host "• You must update any external applications using old credentials" -ForegroundColor White
Write-Host "• Keep backup files safe in case you need to rollback" -ForegroundColor White
Write-Host "• Test thoroughly before deploying to production" -ForegroundColor White

Write-Host "`n💡 TIP: If you want to preserve data, export it first using pg_dump" -ForegroundColor Cyan

Write-Host "`n" + ("=" * 70) -ForegroundColor Green
Write-Host "✅ CREDENTIAL UPDATE COMPLETE!" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Green
