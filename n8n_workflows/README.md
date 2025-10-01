# n8n Workflows for Odoo AI Agent

This folder contains n8n workflow templates for integrating your Coolify-deployed AI agent with various channels.

## Available Workflows

### 1. **whatsapp_with_coolify_ai_agent.json** (Recommended)
**Purpose**: Complete WhatsApp chatbot using Evolution API and your AI agent

**Features**:
- Receives WhatsApp messages via webhook
- Sends messages to Coolify AI agent
- Returns AI responses to WhatsApp
- Handles customer context

**Setup**:
1. Import to n8n
2. Configure Evolution API credentials
3. Set up webhook in Evolution API
4. Test with WhatsApp message

**Use Case**: Production WhatsApp bot for customer inquiries about Odoo data

---

### 2. **simple_test_webhook.json** (For Testing)
**Purpose**: Simple HTTP webhook for testing your AI agent

**Features**:
- Direct HTTP endpoint
- No dependencies (no WhatsApp needed)
- Returns JSON response
- Perfect for development/testing

**Setup**:
1. Import to n8n
2. Activate workflow
3. Copy webhook URL
4. Test with curl or Postman

**Test Command**:
```bash
curl -X POST https://your-n8n.com/webhook/test-ai-agent \
  -H "Content-Type: application/json" \
  -d '{"message": "How many sales orders do we have?"}'
```

**Use Case**: Testing and development before WhatsApp integration

---

### 3. **test version 1.1 copy.json** (Original - Complex)
**Purpose**: Your original complex workflow with multiple tools and agents

**Features**:
- Information extraction with Gemini
- Multiple specialized tools (read/create/update Odoo)
- PostgreSQL chat memory
- Complex formatting and routing
- Predictive analytics

**Note**: This is your existing production workflow. The new workflows are simpler alternatives that use your Coolify AI agent instead of the complex tool chain.

**Use Case**: If you prefer the multi-tool approach with more control

---

## Quick Start Guide

### Step 1: Choose Your Workflow

**For Production (WhatsApp)**:
- Use `whatsapp_with_coolify_ai_agent.json`
- Requires: Evolution API credentials

**For Testing**:
- Use `simple_test_webhook.json`
- No credentials needed

### Step 2: Import to n8n

1. Open n8n
2. Click **"+" (Create new workflow)**
3. Click **"⋮" menu** → **Import from File**
4. Select the workflow JSON file
5. Click **Import**

### Step 3: Configure & Test

**For WhatsApp workflow**:
1. Add Evolution API credentials
2. Copy webhook URL
3. Configure in Evolution API
4. Send test WhatsApp message

**For test workflow**:
1. Activate workflow
2. Copy webhook URL
3. Test with curl/Postman

## Workflow Comparison

| Feature | Simple Test | WhatsApp Bot | Original Complex |
|---------|-------------|--------------|------------------|
| **Complexity** | ⭐ Simple | ⭐⭐ Moderate | ⭐⭐⭐⭐⭐ Very Complex |
| **Setup Time** | 2 minutes | 10 minutes | 30+ minutes |
| **Dependencies** | None | Evolution API | Evolution API, PostgreSQL, Multiple credentials |
| **AI Processing** | Coolify Agent | Coolify Agent | Multiple Gemini models + Tools |
| **Odoo Access** | Full (via agent) | Full (via agent) | Full (via direct tools) |
| **Chat Memory** | No | No (can add) | Yes (PostgreSQL) |
| **WhatsApp** | No | Yes | Yes |
| **Use Case** | Testing/Dev | Production | Advanced/Custom |

## Integration Examples

### Example 1: Test with curl
```bash
# Using simple test webhook
curl -X POST https://your-n8n.com/webhook/test-ai-agent \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me the top 5 customers by revenue"
  }'
```

### Example 2: WhatsApp Integration
```
User sends: "How many products do we have?"
    ↓
Evolution API receives message
    ↓
Webhook triggers n8n workflow
    ↓
n8n calls Coolify AI Agent
    ↓
AI Agent queries Odoo
    ↓
AI Agent formats response
    ↓
n8n receives response
    ↓
Evolution API sends WhatsApp reply
    ↓
User receives: "You have 150 products in inventory..."
```

### Example 3: Add to Existing Workflow

If you have an existing n8n workflow, add these nodes:

```
[Your Node] 
    ↓
HTTP Request
  - Method: POST
  - URL: http://ak08sc4008oo4w04g8os8gg0.129.151.133.251.sslip.io/chat
  - Body: {"message": "{{ $json.question }}"}
    ↓
[Process Response]
```

## Advanced Customizations

### Add Conversation Memory

**Using PostgreSQL**:
1. Add **Postgres Chat Memory** node
2. Configure session key: `{{ $json.customer_phone }}_{{ $json.instance }}`
3. Store/retrieve conversation history
4. Pass history to AI agent

**Using Redis**:
1. Add **Redis** node
2. Store messages with TTL (e.g., 1 hour)
3. Fetch before calling AI agent

### Add Customer Context

Fetch customer data before calling AI:

```javascript
// In a Code node before calling AI
const customerId = await findCustomerByPhone($json.customer_phone);
const customerData = await fetchFromOdoo(customerId);

return {
  json: {
    message: $json.message,
    context: {
      customer_id: customerId,
      customer_name: customerData.name,
      last_order: customerData.last_order_date,
      total_orders: customerData.order_count
    }
  }
};
```

### Add Language Detection

```javascript
// Detect language and pass to AI
const detectLanguage = (text) => {
  // Simple detection or use a library
  if (/[\u0600-\u06FF]/.test(text)) return 'ar'; // Arabic
  return 'en';
};

const language = detectLanguage($json.message);
```

### Handle Media Messages

```javascript
// In Extract Message node
if (body?.data?.message?.imageMessage) {
  return {
    json: {
      message: "User sent an image",
      media_type: "image",
      media_url: body.data.message.imageMessage.url
    }
  };
}
```

## Monitoring & Debugging

### Check AI Agent Health
```bash
curl http://ak08sc4008oo4w04g8os8gg0.129.151.133.251.sslip.io/ping
```

Expected response:
```json
{
  "status": "ok",
  "gemini_connected": true,
  "odoo_connected": true
}
```

### Check n8n Execution Logs
1. Go to n8n **Executions** tab
2. Click on failed execution
3. Check each node's input/output
4. Look for error messages

### Check Coolify Logs
```bash
# In Coolify dashboard
# Go to your service → Logs
# Look for errors or timeout messages
```

## Troubleshooting

### Problem: "Timeout" error
**Solution**: Increase timeout in HTTP Request node to 60000ms (60 seconds)

### Problem: "404 Not Found"
**Solution**: Check Coolify service is running and URL is correct

### Problem: "429 Rate Limit"
**Solution**: Wait 30-60 seconds, or reduce Odoo record limit in app.py

### Problem: No WhatsApp reply
**Solution**: 
1. Check Evolution API credentials
2. Verify webhook is configured
3. Test webhook manually

## Next Steps

1. ✅ Import workflow to n8n
2. ✅ Test with simple webhook first
3. ✅ Then try WhatsApp integration
4. 🔄 Add conversation memory
5. 🔄 Customize responses
6. 🔄 Deploy to production

## Support

For issues:
1. Check this README
2. Review the main integration guide: `N8N_INTEGRATION_GUIDE.md`
3. Test AI agent directly with Postman
4. Check n8n execution logs

---

**Pro Tip**: Start with `simple_test_webhook.json` to verify your AI agent works correctly before setting up WhatsApp integration!
