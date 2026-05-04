# SuryaCaller Full Startup Script for Windows PowerShell

# 1. Load Environment Variables from api/.env
if (Test-Path "api/.env") {
    Write-Host "Loading environment variables from api/.env..." -ForegroundColor Cyan
    Get-Content api/.env | Where-Object { $_ -match '=' -and $_ -notmatch '^#' } | ForEach-Object {
        $name, $value = $_ -split '=', 2
        $name = $name.Trim()
        $value = $value.Trim().Trim('"').Trim("'")
        [System.Environment]::SetEnvironmentVariable($name, $value, 'Process')
    }
} else {
    Write-Error "api/.env file not found!"
    exit 1
}

# 2. Set PYTHONPATH and Encoding
$env:PYTHONPATH = ".;./pipecat/src"
$env:PYTHONIOENCODING = "utf-8"
$python = if (Test-Path ".venv/Scripts/python.exe") { ".venv/Scripts/python.exe" } else { "python" }

# 3. Define services
$services = @(
    @{ Name = "API Server"; Cmd = "$python start_backend.py" },
    @{ Name = "ARQ Worker"; Cmd = "$python -m arq api.tasks.arq.WorkerSettings --custom-log-dict api.tasks.arq.LOG_CONFIG" },
    @{ Name = "Campaign Orchestrator"; Cmd = "$python -m api.services.campaign.campaign_orchestrator" },
    @{ Name = "ARI Manager"; Cmd = "$python -m api.services.telephony.ari_manager" }
)

Write-Host "`nStarting Backend Services..." -ForegroundColor Green

foreach ($service in $services) {
    Write-Host "→ Starting $($service.Name)..."
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:PYTHONPATH='.;./pipecat/src'; `$env:PYTHONIOENCODING='utf-8'; $($service.Cmd)"
}

# 4. Start Frontend
Write-Host "`nStarting Frontend (UI)..." -ForegroundColor Blue
Set-Location ui
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev"
Set-Location ..

Write-Host "`n🚀 All services have been launched in separate terminal windows." -ForegroundColor Cyan
Write-Host "Check the health at http://localhost:8000/api/v1/health"
Write-Host "Access the dashboard at http://localhost:3000"
