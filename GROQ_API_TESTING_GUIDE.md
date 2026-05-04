# 🎙️ SuryaCaller Voice Agent - Groq API Integration Guide

## ✅ Current Status

### Configuration (ALL CORRECT ✓)
- **Groq LLM API Key**: `gsk_...q8yP` ✓ Configured
- **Model**: `llama-3.1-8b-instant` ✓ Set
- **Sarvam TTS**: `bulbul:v2` (anushka voice) ✓ Configured
- **Sarvam STT**: `vittha` ✓ Configured
- **Voice Agent**: Workflow ID 9 - "Professional Customer Service Agent" ✓ Created

### Why Groq Shows "0 API Calls"
The Groq API is **only called during live conversations**. Your voice agent is ready but hasn't been tested yet.

---

## 🚀 How to Trigger Groq API Calls

### Method 1: Browser Test (INSTANT - RECOMMENDED)

This method will immediately call the Groq API when you speak to your agent.

#### Steps:
1. **Open Browser** (Chrome/Edge/Firefox recommended)
   ```
   http://localhost:3000/workflow/9
   ```

2. **If you see "Workflow not found"**:
   - Go back to: `http://localhost:3000/workflow`
   - Find "Professional Customer Service Agent" in the list
   - Click on it from there

3. **Start Testing**:
   - Click the **"Test Workflow"** button (▶ play icon)
   - Allow microphone access when prompted
   - Say: *"Hello, can you help me?"* or any question

4. **Watch the Magic Happen**:
   ```
   You speak → Sarvam STT listens → GROQ LLM thinks → Sarvam TTS speaks
   ```

5. **Verify Groq API Call**:
   - Go to: https://console.groq.com/keys
   - Refresh the page
   - You'll see: **1 API Call** instead of 0!

---

### Method 2: Phone Call (Requires Telephony)

If you have Twilio/Vobiz configured:

1. Configure telephony provider at: `http://localhost:3000/telephony-configurations`

2. Run PowerShell command:
```powershell
$callBody = @{
    workflow_id = 9
    phone_number = "+91XXXXXXXXXX"  # Your test number
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/initiate-call" `
  -Method POST `
  -Headers @{Authorization="Bearer $TOKEN"} `
  -ContentType "application/json" `
  -Body $callBody
```

---

## 📊 What Happens During a Test Call

### Conversation Flow:

```
1. YOU SPEAK
   "Hi, I need help with my account balance"
   
   ↓
   
2. SARVAM STT (Speech-to-Text)
   Converts your speech → text
   Uses: Sarvam vittha model
   
   ↓
   
3. GROQ LLM (Language Intelligence) ← API CALL HAPPENS HERE! 🟢
   Receives: "Hi, I need help with my account balance"
   Processes with: llama-3.1-8b-instant
   Generates: "I'd be happy to help you check your account balance. 
               Could you please provide me with your account number 
               or the email address associated with your account?"
   
   ↓
   ⚡ GROQ API COUNT INCREASES TO 1!
   
4. SARVAM TTS (Text-to-Speech)
   Converts response text → natural speech
   Uses: bulbul:v2 model with anushka voice
   
   ↓
   
5. YOU HEAR RESPONSE
   "I'd be happy to help you check your account balance..."
```

---

## 🎯 Expected Agent Behavior

### Opening Greeting:
> "Hello! Thank you so much for calling today. This is your AI assistant from SuryaCaller. I'm genuinely happy to help you with whatever you need. How are you doing?"

### Conversation Style:
- ✅ **Natural & Human-like**: Uses contractions ("I'm", "you're", "we'll")
- ✅ **Empathetic**: "I understand", "That must be frustrating", "I'm here to help"
- ✅ **Patient**: Lets you speak at your own pace
- ✅ **Contextual**: Remembers what you said, asks follow-up questions
- ✅ **Professional yet Warm**: Friendly but knowledgeable tone

### Sample Conversation:

**You**: "Hi, I'm having trouble with my recent order."

**Agent** (Groq-powered):
> "I understand how concerning that can be. I'd be happy to help you with your order issue. Could you tell me a bit more about what's happening? For example, has your order been delayed, or did you receive a damaged item?"

*(Notice how it's empathetic, asks clarifying questions, and sounds human? That's Groq LLM working!)*

---

## 🔧 Troubleshooting

### Issue: "Workflow not found" when accessing /workflow/9

**Solution 1: Clear Cache**
- Press `Ctrl + Shift + Delete`
- Clear cached images and files
- Press `Ctrl + Shift + R` (hard refresh)

**Solution 2: Access via List**
- Go to: `http://localhost:3000/workflow`
- You'll see all workflows listed
- Click "Professional Customer Service Agent"

**Solution 3: Re-login**
- Go to: `http://localhost:3000/login`
- Login with: `admin@suryacaller.com` / `admin123`
- Then navigate to workflow

---

### Issue: No sound or microphone not working

**Check Browser Permissions**:
- Click the lock icon in address bar
- Ensure Microphone permission is set to "Allow"
- Refresh page and try again

**Check System Settings**:
- Windows: Settings → Privacy → Microphone
- Ensure "Allow apps to access your microphone" is ON

---

### Issue: Agent not responding or slow

**Check Internet Connection**:
- Groq API requires internet access
- Check if you can access external websites

**Check API Keys**:
- Verify Groq key is active: https://console.groq.com/keys
- Ensure it hasn't expired or exceeded rate limits

---

## 📈 Monitoring Groq Usage

After testing, check your usage:

1. **Go to**: https://console.groq.com/keys
2. **Find your key**: `gsk_...q8yP`
3. **Check "Usage (24hrs)"**: Should show > 0 after testing

### Typical API Call Pattern:
- **Each conversation turn** = 1 API call
- **Example**: 5 minute conversation ≈ 10-15 API calls
- **Rate Limits**: Check your Groq plan for limits

---

## 🎭 Testing Scenarios

Try these prompts to see Groq's capabilities:

### Scenario 1: Customer Service
```
"I received a damaged product, what should I do?"
```
Expected: Empathetic response with return/exchange instructions

### Scenario 2: Information Query
```
"What are your business hours?"
```
Expected: Helpful response (may ask which location/service)

### Scenario 3: Technical Support
```
"My app keeps crashing when I try to login"
```
Expected: Troubleshooting steps, asks for error details

### Scenario 4: General Conversation
```
"How's your day going?"
```
Expected: Friendly, natural small talk response

---

## ✅ Success Indicators

You'll know it's working when:

- ✅ Groq dashboard shows increasing API calls
- ✅ Agent responds naturally to ANY topic
- ✅ Responses are contextual and relevant
- ✅ Voice sounds natural (not robotic)
- ✅ Conversation flows smoothly
- ✅ Agent remembers previous statements

---

## 🎉 Quick Start Summary

**RIGHT NOW - Follow These Steps:**

1. Open Chrome/Edge browser
2. Go to: `http://localhost:3000/workflow/9`
3. Click "Test Workflow" button
4. Say: "Hi there! Can you help me?"
5. Listen to Groq-powered response!
6. Check: https://console.groq.com/keys
7. See: **1 API Call** ✅

---

## 📞 Support

If issues persist:
- Check browser console (F12) for errors
- Verify all services running (backend port 8000, frontend port 3000)
- Confirm Groq API key is valid and has quota remaining
- Try different browser (Chrome/Edge recommended)

---

**Your Professional Voice Agent is ready to demonstrate its Groq-powered intelligence! Just start a conversation!** 🚀
