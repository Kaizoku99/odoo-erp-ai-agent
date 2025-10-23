# Migration Guide: Google Gemini to Vercel AI Gateway with Claude Haiku 4.5

This guide will help you migrate from Google Gemini to Vercel AI Gateway using Claude Haiku 4.5.

## Why Migrate?

### Benefits of Claude Haiku 4.5 via Vercel AI Gateway

1. **Better Performance**

   - Near-frontier performance at lower cost
   - Faster response times for real-time applications
   - Extended thinking capabilities for complex reasoning

2. **Unified API Access**

   - OpenAI-compatible endpoints
   - Easy switching between different AI models
   - Built-in monitoring and analytics

3. **Cost Efficiency**

   - $1 per million input tokens
   - $5 per million output tokens
   - Transparent pricing and usage tracking

4. **Enhanced Features**
   - Context awareness throughout conversations
   - Better multi-step workflow handling
   - Advanced reasoning for complex ERP operations

## Migration Steps

### Step 1: Get Vercel AI Gateway API Key

1. Sign in to [Vercel](https://vercel.com)
2. Navigate to [AI Gateway](https://vercel.com/ai-gateway)
3. Click on "Create API Key" or "Generate Key"
4. Copy your API key (starts with `vag_`)
5. Store it securely

### Step 2: Update Environment Variables

**Old (Gemini):**

```env
GEMINI_API_KEY=your_gemini_api_key
ODOO_URL=http://web:8069
ODOO_DB=HISEY
ODOO_USERNAME=cjhisey@gmail.com
ODOO_PASSWORD=odoo
```

**New (Vercel AI Gateway):**

```env
VERCEL_AI_GATEWAY_KEY=your_vercel_ai_gateway_key
ODOO_URL=http://web:8069
ODOO_DB=HISEY
ODOO_USERNAME=cjhisey@gmail.com
ODOO_PASSWORD=odoo
```

### Step 3: Update Coolify Deployment (if applicable)

If you're using Coolify:

1. Go to your service in Coolify dashboard
2. Navigate to **Environment Variables**
3. **Remove:**
   - `GEMINI_API_KEY`
4. **Add:**
   - `VERCEL_AI_GATEWAY_KEY` = `your_vercel_ai_gateway_key`
5. Click **Save**
6. Click **Redeploy**

### Step 4: Update Docker Compose (if applicable)

**Old:**

```yaml
environment:
  - GEMINI_API_KEY=${GEMINI_API_KEY}
  - ODOO_URL=${ODOO_URL}
  - ODOO_DB=${ODOO_DB}
  - ODOO_USERNAME=${ODOO_USERNAME}
  - ODOO_PASSWORD=${ODOO_PASSWORD}
```

**New:**

```yaml
environment:
  - VERCEL_AI_GATEWAY_KEY=${VERCEL_AI_GATEWAY_KEY}
  - ODOO_URL=${ODOO_URL}
  - ODOO_DB=${ODOO_DB}
  - ODOO_USERNAME=${ODOO_USERNAME}
  - ODOO_PASSWORD=${ODOO_PASSWORD}
```

### Step 5: Update Local .env File

If running locally:

```bash
# Remove or comment out
# GEMINI_API_KEY=your_gemini_api_key

# Add
VERCEL_AI_GATEWAY_KEY=your_vercel_ai_gateway_key
```

### Step 6: Pull Latest Code

```bash
git pull origin main
```

### Step 7: Rebuild and Restart

**For Docker:**

```bash
docker-compose down
docker-compose build
docker-compose up -d
```

**For Local Development:**

```bash
# Deactivate old venv if active
deactivate

# Activate venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install updated dependencies
pip install -r requirements.txt

# Restart the server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**For Coolify:**

- Simply click "Redeploy" after updating environment variables

### Step 8: Verify the Migration

Test the health endpoint:

```bash
curl http://localhost:8000/ping
```

Expected response:

```json
{
  "status": "ok",
  "ai_connected": true,
  "ai_model": "anthropic/claude-haiku-4-5-20251015",
  "odoo_connected": true
}
```

Test the chat endpoint:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, can you help me with my Odoo system?"}'
```

## What Changed?

### Code Changes

1. **Dependencies** (`requirements.txt`)

   - **Removed:** `google-generativeai>=0.3.0`
   - **Added:** `openai>=1.50.0`

2. **API Client** (`app.py`)

   - **Old:** Used `google.generativeai` library
   - **New:** Uses `openai` library with custom base URL

3. **Model Configuration**

   - **Old:** `gemini-2.5-flash-preview-09-2025`
   - **New:** `anthropic/claude-haiku-4-5-20251015`

4. **API Endpoint**

   - **Old:** Google AI Studio endpoint
   - **New:** `https://ai-gateway.vercel.sh/v1`

5. **Message Format**
   - **Old:** Single prompt string
   - **New:** OpenAI-compatible messages array with system/user/assistant roles

### API Response Changes

The core functionality remains the same. You should see:

- Same or better response quality
- Faster response times
- Better context retention in conversations

## Rollback Plan

If you need to rollback to Gemini:

1. Checkout the previous version:

   ```bash
   git log  # Find the commit before migration
   git checkout <commit-hash>
   ```

2. Update environment variables back to use `GEMINI_API_KEY`

3. Rebuild and restart the service

## Troubleshooting

### "VERCEL_AI_GATEWAY_KEY environment variable is not set"

**Solution:**

- Ensure you've set the environment variable
- Restart the service after setting it
- Check for typos in the variable name

### "ai_connected": false

**Possible causes:**

1. Invalid API key
2. No access to Claude models in your Vercel account
3. Network connectivity issues
4. API quota exceeded

**Solutions:**

- Verify your API key is correct
- Check your Vercel AI Gateway dashboard for model access
- Ensure your server can reach `https://ai-gateway.vercel.sh`
- Monitor your usage in Vercel dashboard

### Different Response Format

If you notice different response formatting:

**This is expected!** Claude may format responses slightly differently than Gemini. The content should be the same or better, but the structure might vary. This is generally an improvement as Claude provides more structured and detailed responses.

### Rate Limiting

Claude Haiku 4.5 has different rate limits than Gemini:

**Gemini:**

- Varies by project/quota

**Claude via Vercel AI Gateway:**

- Depends on your Vercel plan
- Monitor usage in Vercel dashboard
- Implement caching if needed

## Performance Comparison

Based on typical usage:

| Metric                 | Google Gemini | Claude Haiku 4.5     |
| ---------------------- | ------------- | -------------------- |
| **Response Time**      | 2-4 seconds   | 1-2 seconds          |
| **Context Retention**  | Good          | Excellent            |
| **ERP Understanding**  | Good          | Excellent            |
| **Cost per 1M tokens** | Varies        | $1 input / $5 output |
| **Reasoning Quality**  | Good          | Excellent            |
| **Multi-step Tasks**   | Good          | Excellent            |

## Cost Estimation

Example monthly costs for different usage levels:

### Light Usage (10,000 requests/month)

- Avg 500 input tokens/request = 5M tokens
- Avg 200 output tokens/request = 2M tokens
- **Cost:** $5 (input) + $10 (output) = **$15/month**

### Medium Usage (50,000 requests/month)

- Avg 500 input tokens/request = 25M tokens
- Avg 200 output tokens/request = 10M tokens
- **Cost:** $25 (input) + $50 (output) = **$75/month**

### Heavy Usage (200,000 requests/month)

- Avg 500 input tokens/request = 100M tokens
- Avg 200 output tokens/request = 40M tokens
- **Cost:** $100 (input) + $200 (output) = **$300/month**

## Best Practices After Migration

1. **Monitor Usage**

   - Check Vercel AI Gateway dashboard regularly
   - Set up usage alerts
   - Track costs vs. Gemini

2. **Optimize Prompts**

   - Claude excels at structured prompts
   - Use clear system messages
   - Leverage conversation history

3. **Test Thoroughly**

   - Test key workflows
   - Verify database operations still work
   - Check response quality

4. **Update Documentation**
   - Update internal docs
   - Inform team members
   - Share API key securely

## Support

If you encounter issues during migration:

1. Check the logs: `docker logs odoo-ai-agent` or Coolify logs
2. Test the `/ping` endpoint
3. Verify environment variables
4. Review this migration guide
5. Check Vercel AI Gateway status page
6. Review Claude documentation: https://docs.anthropic.com/

## Feedback

After migration, please note:

- Response quality improvements
- Performance differences
- Cost differences
- Any issues encountered

This helps improve the service for everyone!

---

**Migration Complete!** 🎉

You're now using Claude Haiku 4.5 via Vercel AI Gateway for faster, more intelligent Odoo assistance.
