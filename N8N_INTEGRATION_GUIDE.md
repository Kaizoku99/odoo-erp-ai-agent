# n8n Integration Guide - Coolify AI Agent with WhatsApp

## Overview

This guide explains how to integrate your Coolify-deployed AI agent with n8n and WhatsApp via Evolution API.

## Architecture

```
WhatsApp Message → n8n Webhook → Extract Message → Call AI Agent → Format Response → Send Reply
```

## Setup Instructions

### 1. Import Workflow to n8n

1. Open your n8n instance
2. Click **"+"** to create a new workflow
3. Click the **three dots menu** (⋮) → **Import from File**
4. Select the file: `n8n_workflows/whatsapp_with_coolify_ai_agent.json`
5. Click **Import**

### 2. Configure Evolution API Credentials

1. In the **"Send WhatsApp Reply"** node, click on **"Credential to connect with"**
2. Create new credentials:
   - **Name**: Evolution API
   - **API URL**: Your Evolution API URL
   - **API Key**: Your Evolution API key
3. Click **Save**

### 3. Set Up Webhook

1. Click on the **"WhatsApp Webhook"** node
2. Copy the **Production URL** (will look like: `https://your-n8n.com/webhook/whatsapp-odoo-ai`)
3. Configure this webhook URL in your Evolution API instance:
   - Go to Evolution API settings
   - Set webhook URL for message events
   - Enable webhook for incoming messages

### 4. Test the Workflow

1. Click **"Execute Workflow"** button in n8n
2. Send a message to your WhatsApp number
3. The workflow should:
   - Receive the message
   - Send it to your Coolify AI agent
   - Get a response from the AI
   - Reply back on WhatsApp

## Workflow Nodes Explained

### 1. WhatsApp Webhook
- **Purpose**: Receives incoming WhatsApp messages from Evolution API
- **Path**: `/webhook/whatsapp-odoo-ai`
- **Method**: POST

### 2. Extract Message
- **Purpose**: Parses the webhook payload and extracts:
  - Message text
  - Customer phone number
  - Customer name
  - Instance ID
- **Type**: Code node (JavaScript)

### 3. Call Coolify AI Agent
- **Purpose**: Sends the message to your AI agent
- **URL**: `http://ak08sc4008oo4w04g8os8gg0.129.151.133.251.sslip.io/chat`
- **Method**: POST
- **Body**:
  ```json
  {
    "message": "User's question",
    "context": {
      "customer_name": "Customer Name",
      "customer_phone": "1234567890"
    },
    "conversation_history": []
  }
  ```
- **Timeout**: 60 seconds (AI processing can take time)

### 4. Format Response
- **Purpose**: Extracts the AI response and prepares it for WhatsApp
- **Type**: Code node (JavaScript)

### 5. Send WhatsApp Reply
- **Purpose**: Sends the AI's response back to the customer via WhatsApp
- **Type**: Evolution API node

## Adding Conversation Memory (Optional)

To add conversation history tracking:

### Option 1: Use PostgreSQL Memory

1. Add a **Postgres Chat Memory** node
2. Configure with your PostgreSQL credentials
3. Set session key: `{{ $('Extract Message').item.json.session_key }}`
4. Store conversation history per customer

### Option 2: Modify AI Agent Call

Update the HTTP Request body to include conversation history:

```javascript
// In "Extract Message" node, fetch previous messages from database
const previousMessages = await fetchFromDatabase($json.session_key);

// In "Call Coolify AI Agent" node:
{
  "message": "{{ $json.message }}",
  "context": {
    "customer_name": "{{ $json.customer_name }}"
  },
  "conversation_history": previousMessages
}
```

## Customization Options

### 1. Add Customer Context
Enhance the context sent to the AI:

```json
{
  "message": "User question",
  "context": {
    "customer_name": "John Doe",
    "customer_phone": "1234567890",
    "customer_id": 123,
    "last_order_date": "2025-09-30",
    "preferred_language": "en"
  }
}
```

### 2. Add Error Handling

Add an **IF node** after "Call Coolify AI Agent":

```javascript
// Check if AI response is valid
{{ $json.response !== undefined && $json.response.length > 0 }}
```

If false, send a fallback message:
```
"Sorry, I'm having trouble processing your request. Please try again."
```

### 3. Add Typing Indicator

Before calling the AI agent, send a "typing" indicator:

```javascript
// Add Evolution API node: "Send Typing"
// Resource: presence-api
// Action: Set presence (typing...)
```

### 4. Handle Long Responses

If AI response is very long, split it:

```javascript
// In "Format Response" node
const response = $input.first().json.response;
const maxLength = 4000; // WhatsApp message limit

if (response.length > maxLength) {
  // Split into multiple messages
  const messages = [];
  for (let i = 0; i < response.length; i += maxLength) {
    messages.push(response.substring(i, i + maxLength));
  }
  return messages.map(msg => ({ json: { message: msg, ...otherData } }));
}
```

## Troubleshooting

### Issue: No response from AI agent
**Solution**: 
- Check if Coolify service is running
- Test the `/ping` endpoint: `curl http://ak08sc4008oo4w04g8os8gg0.129.151.133.251.sslip.io/ping`
- Increase timeout in HTTP Request node

### Issue: WhatsApp not replying
**Solution**:
- Verify Evolution API credentials
- Check webhook is properly configured
- Test Evolution API connection manually

### Issue: AI responses are slow
**Solution**:
- The AI agent fetches 100 records per module (can be slow)
- Consider reducing limit in `app.py`: `context = get_odoo_context(limit_records=20)`
- Add timeout handling in n8n

### Issue: Rate limit errors (429)
**Solution**:
- You're hitting Gemini API quota
- Wait 30-60 seconds between requests
- Consider upgrading Gemini API plan
- Add rate limiting in n8n (delay between messages)

## Advanced: Direct Odoo Integration

If you want to bypass the AI agent for simple queries, add these nodes:

1. **IF node**: Check if question is simple (e.g., "How many orders?")
2. **Odoo node**: Direct query to Odoo
3. **Format node**: Format simple response
4. Else: Call AI agent for complex queries

## API Endpoints Reference

### Coolify AI Agent

**Health Check:**
```bash
GET http://ak08sc4008oo4w04g8os8gg0.129.151.133.251.sslip.io/ping
```

**Chat:**
```bash
POST http://ak08sc4008oo4w04g8os8gg0.129.151.133.251.sslip.io/chat
Content-Type: application/json

{
  "message": "How many sales orders do we have?",
  "context": {},
  "conversation_history": []
}
```

## Next Steps

1. ✅ Import workflow to n8n
2. ✅ Configure Evolution API credentials
3. ✅ Set up webhook in Evolution API
4. ✅ Test with a WhatsApp message
5. 🔄 Add conversation memory (optional)
6. 🔄 Customize error handling
7. 🔄 Deploy to production

## Support

If you encounter issues:
1. Check n8n execution logs
2. Check Coolify application logs
3. Test AI agent directly with Postman/curl
4. Verify Evolution API is receiving webhooks

---

**Note**: Remember to commit and push changes:
```bash
git add .
git commit -m "Add n8n integration with Coolify AI agent"
git push origin main
```
