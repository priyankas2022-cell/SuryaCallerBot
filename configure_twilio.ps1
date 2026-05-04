# SuryaCaller - Configure Twilio for Phone Calls
# This script configures Twilio as your telephony provider

Write-Host "`n📞 CONFIGURING TWILIO FOR PHONE CALLS" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Gray

# Step 1: Login to get token
Write-Host "`nStep 1: Authenticating..." -ForegroundColor Yellow
try {
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{"email":"admin@suryacaller.com","password":"admin123"}'
    
    $TOKEN = ($loginResponse.Content | ConvertFrom-Json).token
    Write-Host "✓ Authentication successful!" -ForegroundColor Green
} catch {
    Write-Host "✗ Authentication failed! Please check credentials." -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Gray
    exit 1
}

# Step 2: Get Twilio credentials from user
Write-Host "`nStep 2: Enter Twilio Credentials" -ForegroundColor Yellow
Write-Host "Don't have Twilio? Sign up at: https://www.twilio.com/try-twilio" -ForegroundColor Gray

$accountSid = Read-Host "  Account SID (e.g., ACxxxxxxxxxxxxx)"
$authToken = Read-Host "  Auth Token" -AsSecureString
$fromNumber = Read-Host "  Twilio Phone Number (e.g., +1234567890)"

# Convert secure string to plain text
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($authToken)
$PlainAuthToken = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# Step 3: Create configuration
Write-Host "`nStep 3: Creating Twilio Configuration..." -ForegroundColor Yellow

$twilioConfig = @{
    provider_type = "twilio"
    config = @{
        account_sid = $accountSid
        auth_token = $PlainAuthToken
        from_numbers = @($fromNumber)
    }
} | ConvertTo-Json -Depth 5

Write-Host "Configuration created:" -ForegroundColor Gray
Write-Host "  Provider: twilio" -ForegroundColor Gray
Write-Host "  Account SID: $($accountSid.Substring(0,8))..." -ForegroundColor Gray
Write-Host "  Phone Number: $fromNumber" -ForegroundColor Gray

# Step 4: Send to backend
Write-Host "`nStep 4: Configuring SuryaCaller Backend..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/telephony-configurations" `
        -Method POST `
        -Headers @{Authorization="Bearer $TOKEN"; "Content-Type"="application/json"} `
        -Body $twilioConfig
    
    Write-Host "✓ Twilio configured successfully!" -ForegroundColor Green
    Write-Host "`nResponse from server:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 3 | Write-Host
} catch {
    Write-Host "✗ Configuration failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Gray
    $errorBody = $_.ErrorDetails.Message
    if ($errorBody) {
        Write-Host "Details: $($errorBody | ConvertFrom-Json | ConvertTo-Json)" -ForegroundColor Gray
    }
    exit 1
}

# Step 5: Test configuration
Write-Host "`nStep 5: Verifying Configuration..." -ForegroundColor Yellow

try {
    $configCheck = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/telephony-configurations" `
        -Headers @{Authorization="Bearer $TOKEN"}
    
    if ($configCheck.Count -gt 0) {
        $twilioConfigured = $configCheck | Where-Object { $_.provider_type -eq "twilio" }
        if ($twilioConfigured) {
            Write-Host "✓ Twilio is active and ready!" -ForegroundColor Green
            Write-Host "  Status: $($twilioConfigured.status)" -ForegroundColor Gray
            Write-Host "  Phone Numbers: $($twilioConfigured.phone_numbers -join ', ')" -ForegroundColor Gray
        } else {
            Write-Host "⚠ Twilio configured but not found in list" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠ No configurations found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Could not verify configuration" -ForegroundColor Yellow
}

# Final summary
Write-Host "`n" + ("=" * 70) -ForegroundColor Green
Write-Host "🎉 TWILIO CONFIGURATION COMPLETE!" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Green

Write-Host "`n✅ WHAT YOU CAN DO NOW:" -ForegroundColor Cyan
Write-Host "  1. Make phone calls with your AI agent" -ForegroundColor White
Write-Host "  2. Customers can call your workflow directly" -ForegroundColor White
Write-Host "  3. Receive call transcripts and recordings" -ForegroundColor White

Write-Host "`n📞 MAKE YOUR FIRST CALL:" -ForegroundColor Cyan
Write-Host "Run this command (replace with real number):" -ForegroundColor Gray
Write-Host @"

`$callBody = @{
    workflow_id = 10
    phone_number = "+91_YOUR_TEST_NUMBER"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/initiate-call" `
    -Method POST `
    -Headers @{Authorization="Bearer `$TOKEN"} `
    -ContentType "application/json" `
    -Body `$callBody

"@

Write-Host "`n🎯 TEST IN BROWSER (No phone needed):" -ForegroundColor Cyan
Write-Host "  http://localhost:3000/workflow/10 → Click 'Test Workflow'" -ForegroundColor Gray

Write-Host "`n📊 CHECK TWILIO DASHBOARD:" -ForegroundColor Cyan
Write-Host "  https://console.twilio.com" -ForegroundColor Gray
Write-Host "  View call logs, usage, and billing" -ForegroundColor Gray

Write-Host "`n" + ("=" * 70) -ForegroundColor Green
