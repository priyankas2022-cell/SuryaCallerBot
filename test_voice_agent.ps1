# SuryaCaller - Professional Voice Agent Test Script
# This script tests your Groq + Sarvam powered voice agent

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "🎙️ SURYACALLER VOICE AGENT - DIRECT API TEST" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan

# Re-authenticate to get fresh token
Write-Host "`n[1/4] Authenticating..." -ForegroundColor Yellow
try {
    $loginResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{"email":"admin@suryacaller.com","password":"admin123"}' `
        -UseBasicParsing
    
    $TOKEN = ($loginResponse.Content | ConvertFrom-Json).token
    Write-Host "  ✓ Authentication successful" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Authentication failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Fetch workflow details
Write-Host "`n[2/4] Fetching voice agent details..." -ForegroundColor Yellow
try {
    $workflowResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/workflow/fetch/9" `
        -Headers @{Authorization="Bearer $TOKEN"}
    
    Write-Host "  ✓ Agent found: $($workflowResponse.name)" -ForegroundColor Green
    Write-Host "    ID: $($workflowResponse.id)" -ForegroundColor Gray
    Write-Host "    Status: $($workflowResponse.status)" -ForegroundColor Gray
    Write-Host "    Nodes: $($workflowResponse.workflow_definition.nodes.Count)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Workflow not found in backend" -ForegroundColor Red
    exit 1
}

# Check model configuration
Write-Host "`n[3/4] Checking AI model configuration..." -ForegroundColor Yellow
try {
    $configResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/user/configurations/user" `
        -Headers @{Authorization="Bearer $TOKEN"}
    
    Write-Host "  ✓ Models configured:" -ForegroundColor Green
    Write-Host "    LLM: $($configResponse.llm.provider) ($($configResponse.llm.model))" -ForegroundColor Gray
    Write-Host "    TTS: $($configResponse.tts.provider) ($($configResponse.tts.model), Voice: $($configResponse.tts.voice))" -ForegroundColor Gray
    Write-Host "    STT: $($configResponse.stt.provider) ($($configResponse.stt.model))" -ForegroundColor Gray
} catch {
    Write-Host "  ⚠ Could not fetch model configuration" -ForegroundColor Yellow
}

# Display testing options
Write-Host "`n[4/4] TESTING OPTIONS FOR YOUR VOICE AGENT:" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Cyan

Write-Host "`n📱 OPTION 1: WEBRTC BROWSER TEST (RECOMMENDED - No Setup Required)" -ForegroundColor White
Write-Host "-" * 70
Write-Host "This method uses your browser's microphone and speakers."
Write-Host "Perfect for testing the AI conversation immediately!`n"

Write-Host "Steps:" -ForegroundColor Cyan
Write-Host "  1. Open this URL in Chrome/Edge/Firefox:" -ForegroundColor Gray
Write-Host "     http://localhost:3000/workflow/9" -ForegroundColor Cyan
Write-Host ""
Write-Host "  2. If you see 'Workflow not found':" -ForegroundColor Yellow
Write-Host "     • Click the back button" -ForegroundColor Gray
Write-Host "     • Go to: http://localhost:3000/workflow" -ForegroundColor Cyan
Write-Host "     • Find 'Professional Customer Service Agent' in the list" -ForegroundColor Gray
Write-Host "     • Click on it from there" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Once loaded, click the 'Test Workflow' button (▶ icon)" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Allow microphone access when prompted" -ForegroundColor Gray
Write-Host ""
Write-Host "  5. Start talking! The agent will respond naturally using:" -ForegroundColor Gray
Write-Host "     • Groq LLM for intelligent responses" -ForegroundColor Gray
Write-Host "     • Sarvam TTS (anushka voice) for natural speech" -ForegroundColor Gray
Write-Host "     • Sarvam STT for accurate transcription" -ForegroundColor Gray

Write-Host "`n📞 OPTION 2: DIRECT PHONE CALL (Requires Telephony Provider)" -ForegroundColor White
Write-Host "-" * 70
Write-Host "To make actual phone calls, you need Twilio/Vobiz credentials.`n"

Write-Host "Quick Setup:" -ForegroundColor Cyan
Write-Host "  1. Go to: http://localhost:3000/telephony-configurations" -ForegroundColor Gray
Write-Host "  2. Configure one of: Twilio, Vobiz, Cloudonix, or Looptalk" -ForegroundColor Gray
Write-Host "  3. Then run this PowerShell command:" -ForegroundColor Gray

$testCommand = @"
`$callBody = @{
    workflow_id = 9
    phone_number = "+91XXXXXXXXXX"  # Replace with test number
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/initiate-call" `
  -Method POST `
  -Headers @{Authorization="Bearer `$TOKEN"} `
  -ContentType "application/json" `
  -Body `$callBody
"@

Write-Host $testCommand -ForegroundColor Yellow

Write-Host "`n🧪 OPTION 3: API TESTING (For Developers)" -ForegroundColor White
Write-Host "-" * 70
Write-Host "Test the backend APIs directly:`n"

Write-Host "a) Test Backend Health:" -ForegroundColor Cyan
Write-Host '   curl http://localhost:8000/api/v1/health' -ForegroundColor Gray

Write-Host "`nb) Get Workflow Details:" -ForegroundColor Cyan
Write-Host "   curl -H `"Authorization: Bearer TOKEN`" http://localhost:8000/api/v1/workflow/fetch/9" -ForegroundColor Gray

Write-Host "`nc) Validate Configuration:" -ForegroundColor Cyan
Write-Host '   curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/v1/user/configurations/user/validate' -ForegroundColor Gray

Write-Host "`n" + ("=" * 70) -ForegroundColor Green
Write-Host "✨ WHAT TO EXPECT FROM YOUR VOICE AGENT:" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Green

Write-Host "`n🎭 Greeting (Opening):" -ForegroundColor Yellow
Write-Host '  "Hello! Thank you so much for calling today. This is your' -ForegroundColor White
Write-Host '   AI assistant from SuryaCaller. I'm genuinely happy to help' -ForegroundColor White
Write-Host '   you with whatever you need. How are you doing?"' -ForegroundColor White

Write-Host "`n💬 Conversation Style:" -ForegroundColor Yellow
Write-Host "  ✓ Natural, human-like responses (not robotic)" -ForegroundColor Gray
Write-Host "  ✓ Empathetic and patient listening" -ForegroundColor Gray
Write-Host "  ✓ Uses phrases like 'I understand', 'Let me help you'" -ForegroundColor Gray
Write-Host "  ✓ Asks thoughtful follow-up questions" -ForegroundColor Gray
Write-Host "  ✓ Allows interruptions (natural conversation flow)" -ForegroundColor Gray
Write-Host "  • Responds contextually to ANY topic" -ForegroundColor Gray
Write-Host "  • Professional yet warm and friendly tone" -ForegroundColor Gray

Write-Host "`n🎯 Closing:" -ForegroundColor Yellow
Write-Host '  "It's been my pleasure helping you today! Is there anything' -ForegroundColor White
Write-Host '   else I can assist you with? If not, have a wonderful day' -ForegroundColor White
Write-Host '   and thank you for calling. Take care! Goodbye!"' -ForegroundColor White

Write-Host "`n" + ("=" * 70) -ForegroundColor Green
Write-Host "🚀 QUICK START:" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Green
Write-Host "`n👉 EASIEST METHOD: Open http://localhost:3000/workflow/9" -ForegroundColor Yellow
Write-Host "   and click 'Test Workflow' to start talking NOW!`n" -ForegroundColor Gray
