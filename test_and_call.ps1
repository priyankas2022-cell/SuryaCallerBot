# SuryaCaller - Test Model Configuration and Generate Call

Write-Host "`n" + ("=" * 70)
Write-Host "SURYACALLER - Model Test & Call Generation"
Write-Host ("=" * 70) + "`n"

# Use existing TOKEN from previous session
if (-not $TOKEN) {
    Write-Host "ERROR: TOKEN variable not set. Please run the authentication first." -ForegroundColor Red
    Write-Host "Run this command first:" -ForegroundColor Yellow
    Write-Host '$signupResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/signup" -Method POST -ContentType "application/json" -Body ''{"email":"admin@suryacaller.com","password":"admin123","name":"Admin User"}'' -UseBasicParsing' -ForegroundColor Gray
    Write-Host '$TOKEN = ($signupResponse.Content | ConvertFrom-Json).token' -ForegroundColor Gray
    exit 1
}

Write-Host "[Step 1] Fetching current configuration..." -ForegroundColor Cyan
$configResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/user/configurations/user" `
    -Method GET `
    -Headers @{Authorization="Bearer $TOKEN"} `
    -UseBasicParsing

$config = $configResponse.Content | ConvertFrom-Json
Write-Host "  LLM: $($config.llm.provider) / $($config.llm.model)" -ForegroundColor Green
Write-Host "  TTS: $($config.tts.provider) / $($config.tts.model) (Voice: $($config.tts.voice))" -ForegroundColor Green
Write-Host "  STT: $($config.stt.provider) / $($config.stt.model)`n" -ForegroundColor Green

Write-Host "[Step 2] Creating test workflow..." -ForegroundColor Cyan
$workflowName = "Test Voice Agent - $(Get-Date -Format 'yyyyMMdd HHmmss')"

# Create workflow definition JSON
$workflowDefinitionJson = @"
{
    "nodes": [
        {
            "id": "1",
            "type": "startCall",
            "position": {"x": 0, "y": 0},
            "data": {
                "name": "Start",
                "prompt": "Hello! This is a test call from SuryaCaller AI voice agent. How can I help you today?",
                "is_start": true,
                "allow_interrupt": false,
                "add_global_prompt": false
            }
        },
        {
            "id": "2",
            "type": "endCall",
            "position": {"x": 0, "y": 200},
            "data": {
                "name": "End",
                "prompt": "Thank you for your time. Goodbye!",
                "is_end": true
            }
        }
    ],
    "edges": [
        {
            "id": "1-2",
            "source": "1",
            "target": "2",
            "data": {"label": "End", "condition": "End the call"}
        }
    ]
}
"@

try {
    $createResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/workflow/create/definition" `
        -Method POST `
        -Headers @{
            Authorization="Bearer $TOKEN"
            "Content-Type"="application/json"
        } `
        -Body "{`"name`":`"$workflowName`",`"workflow_definition`":$workflowDefinitionJson}" `
        -UseBasicParsing
    
    $workflow = $createResponse.Content | ConvertFrom-Json
    $workflowId = $workflow.id
    
    Write-Host "  ✓ Workflow created successfully!" -ForegroundColor Green
    Write-Host "    ID: $workflowId" -ForegroundColor Cyan
    Write-Host "    Name: $workflowName`n" -ForegroundColor Cyan
    
} catch {
    Write-Host "  ✗ Failed to create workflow: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "[Step 3] Checking telephony status..." -ForegroundColor Cyan
try {
    $telephonyResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/telephony" `
        -Method GET `
        -Headers @{Authorization="Bearer $TOKEN"} `
        -UseBasicParsing
    
    $telephonyConfigs = $telephonyResponse.Content | ConvertFrom-Json
    if ($telephonyConfigs -and $telephonyConfigs.Count -gt 0) {
        Write-Host "  ✓ Telephony configured: $($telephonyConfigs[0].provider)`n" -ForegroundColor Green
        $telephonyConfigured = $true
    } else {
        $telephonyConfigured = $false
    }
} catch {
    $telephonyConfigured = $false
    Write-Host "  ⚠ No telephony provider configured`n" -ForegroundColor Yellow
}

# Display results
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "YOUR AI VOICE AGENT IS READY!" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Cyan

Write-Host "`nWORKFLOW DETAILS:" -ForegroundColor White
Write-Host "  Workflow ID: $workflowId" -ForegroundColor Gray
Write-Host "  Name: $workflowName" -ForegroundColor Gray
Write-Host "  Status: Active" -ForegroundColor Green

Write-Host "`nCONFIGURED MODELS:" -ForegroundColor White
Write-Host "  LLM (Language): $($config.llm.provider) - $($config.llm.model)" -ForegroundColor Gray
Write-Host "  TTS (Speech):   $($config.tts.provider) - $($config.tts.model) (Voice: $($config.tts.voice))" -ForegroundColor Gray
Write-Host "  STT (Transcription): $($config.stt.provider) - $($config.stt.model)" -ForegroundColor Gray

Write-Host "`nAGENT SCRIPT:" -ForegroundColor White
Write-Host '  "Hello! This is a test call from SuryaCaller AI voice agent.' -ForegroundColor Yellow
Write-Host '   How can I help you today?"' -ForegroundColor Yellow
Write-Host '  "Thank you for your time. Goodbye!"' -ForegroundColor Yellow

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "HOW TO TEST YOUR VOICE AGENT:" -ForegroundColor White
Write-Host ("=" * 70) -ForegroundColor Cyan

Write-Host "`nOPTION 1: WebRTC Browser Test (RECOMMENDED - No phone needed)" -ForegroundColor Cyan
Write-Host "  1. Open this URL in your browser:" -ForegroundColor Gray
Write-Host "     http://localhost:3000/workflow/$workflowId" -ForegroundColor Cyan
Write-Host "  2. Click 'Test Workflow' button" -ForegroundColor Gray
Write-Host "  3. Allow microphone access when prompted" -ForegroundColor Gray
Write-Host "  4. Talk to your AI agent through your browser!`n" -ForegroundColor Gray

if ($telephonyConfigured) {
    Write-Host "OPTION 2: Direct Phone Call" -ForegroundColor Cyan
    Write-Host "  Run this PowerShell command:" -ForegroundColor Gray
    Write-Host @"
  `$body = @{
      workflow_id = $workflowId
      phone_number = "+91XXXXXXXXXX"  # Replace with actual number
  } | ConvertTo-Json
  
  Invoke-RestMethod -Uri "http://localhost:8000/api/v1/initiate-call" `
    -Method POST `
    -Headers @{Authorization="Bearer `$TOKEN"} `
    -ContentType "application/json" `
    -Body `$body
"@
    Write-Host ""
} else {
    Write-Host "OPTION 2: Configure Telephony (For phone calls)" -ForegroundColor Cyan
    Write-Host "  1. Visit: http://localhost:3000/telephony-configurations" -ForegroundColor Gray
    Write-Host "  2. Configure Twilio, Vobiz, Cloudonix, or Looptalk" -ForegroundColor Gray
    Write-Host "  3. Then you can make calls to real phone numbers`n" -ForegroundColor Gray
}

Write-Host "OPTION 3: Create a Campaign (Bulk calling)" -ForegroundColor Cyan
Write-Host "  1. Go to: http://localhost:3000/campaigns" -ForegroundColor Gray
Write-Host "  2. Create new campaign with this workflow" -ForegroundColor Gray
Write-Host "  3. Add contact list" -ForegroundColor Gray
Write-Host "  4. System will auto-call all contacts`n" -ForegroundColor Gray

Write-Host ("=" * 70) -ForegroundColor Green
Write-Host "SUCCESS! Your SuryaCaller voice agent is ready to use." -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Green
Write-Host "`nQuick Start: http://localhost:3000/workflow/$workflowId`n" -ForegroundColor Green
