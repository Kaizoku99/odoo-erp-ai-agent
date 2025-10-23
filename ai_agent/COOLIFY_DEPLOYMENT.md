# Deploying Odoo AI Agent to Coolify

This guide will help you deploy the standalone AI Agent service to Coolify. The AI agent will connect to your existing Odoo instance and provide AI-powered assistance through a REST API.

## Prerequisites

- A Coolify account and server
- An existing Odoo instance (can be anywhere - local, cloud, or another server)
- A Vercel AI Gateway API key ([Get one here](https://vercel.com/ai-gateway))
- Your Odoo database credentials

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│    n8n      │─────▶│  AI Agent    │─────▶│    Odoo     │
│  Workflow   │      │  (Coolify)   │      │  Instance   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │Vercel AI     │
                     │Gateway       │
                     │(Claude 4.5)  │
                     └──────────────┘
```

The AI Agent acts as a bridge between n8n (or any other client) and your Odoo system, using Claude Haiku 4.5 via Vercel AI Gateway to translate natural language into Odoo operations.

## Step 1: Prepare Your Repository

1. **Push your code to a Git repository** (GitHub, GitLab, Bitbucket, etc.)
   ```bash
   git add .
   git commit -m "Configure AI agent for Coolify deployment"
   git push origin main
   ```

## Step 2: Create a New Service in Coolify

1. Log in to your Coolify dashboard
2. Click **"+ New Resource"**
3. Select **"Public Repository"** or connect your private repository
4. Enter your repository URL
5. Select the branch (e.g., `main`)

## Step 3: Configure the Service

### Basic Settings

- **Name**: `odoo-ai-agent` (or your preferred name)
- **Build Pack**: Docker (Dockerfile)
- **Dockerfile Location**: `ai_agent/Dockerfile`
- **Port**: `8000` (the app runs on this port)
- **Publish Port**: Enable and set to `8000` (or any available port)

### Build Configuration

- **Base Directory**: `/ai_agent` (if your Dockerfile is in the ai_agent folder)
- Or set **Dockerfile Path**: `./ai_agent/Dockerfile`

## Step 4: Configure Environment Variables

In Coolify, add the following environment variables:

| Variable Name           | Value                          | Description                            |
| ----------------------- | ------------------------------ | -------------------------------------- |
| `ODOO_URL`              | `http://your-odoo-server:8069` | Full URL to your Odoo instance         |
| `ODOO_DB`               | `your_database_name`           | Your Odoo database name                |
| `ODOO_USERNAME`         | `your_username@email.com`      | Odoo user with appropriate permissions |
| `ODOO_PASSWORD`         | `your_password`                | Odoo user password                     |
| `VERCEL_AI_GATEWAY_KEY` | `your_vercel_gateway_key`      | Vercel AI Gateway API key              |

### Important Notes:

- **ODOO_URL**: Must be accessible from the Coolify server

  - If Odoo is on the same Coolify server, use internal networking (e.g., `http://odoo-service:8069`)
  - If Odoo is external, ensure firewall rules allow the Coolify server to access it
  - Use the full URL including `http://` or `https://`

- **ODOO_DB**: The exact database name (case-sensitive)

- **ODOO_USERNAME**: A user with API access rights. Recommended permissions:

  - Sales Manager (for sales operations)
  - Inventory Manager (for stock operations)
  - Accounting Manager (for financial operations)
  - Or an Administrator account

- **VERCEL_AI_GATEWAY_KEY**: Get your API key from [Vercel AI Gateway](https://vercel.com/ai-gateway)
  - Sign in to your Vercel account
  - Navigate to the AI Gateway section
  - Generate a new API key
  - The gateway will use Claude Haiku 4.5 model for fast and efficient AI responses

## Step 5: Deploy

1. Click **"Deploy"** in Coolify
2. Monitor the build logs
3. Wait for the deployment to complete (usually 2-5 minutes)

## Step 6: Verify the Deployment

Once deployed, test the service:

### Test the Health Endpoint

```bash
curl https://your-ai-agent-url.coolify.app/ping
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

### Test the Chat Endpoint

```bash
curl -X POST https://your-ai-agent-url.coolify.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How many sales orders do we have?"}'
```

Expected response:

```json
{
  "response": "Based on the current data, you have 15 sales orders..."
}
```

## Step 7: Use in n8n

Now you can use this AI Agent in your n8n workflow:

### HTTP Request Node Configuration

- **Method**: POST
- **URL**: `https://your-ai-agent-url.coolify.app/chat`
- **Authentication**: None (or add your own if needed)
- **Headers**:
  - `Content-Type`: `application/json`
- **Body**:
  ```json
  {
    "message": "{{ $json.question }}",
    "context": {},
    "conversation_history": []
  }
  ```

### Example n8n Workflow Setup

1. **Webhook Node**: Receives questions
2. **HTTP Request Node**: Sends to AI Agent (configured as above)
3. **Code Node** (optional): Format the response
4. **Response Node**: Send back to the caller

## API Endpoints

### GET /ping

Health check endpoint

**Response:**

```json
{
  "status": "ok",
  "ai_connected": true,
  "ai_model": "anthropic/claude-haiku-4-5-20251015",
  "odoo_connected": true
}
```

### POST /chat

Main endpoint for AI interactions

**Request Body:**

```json
{
  "message": "Your question here",
  "context": {},
  "conversation_history": [
    { "role": "user", "content": "Previous message" },
    { "role": "assistant", "content": "Previous response" }
  ]
}
```

**Response:**

```json
{
  "response": "AI-generated response with Odoo data"
}
```

## Troubleshooting

### Connection Issues

1. **"VERCEL_AI_GATEWAY_KEY environment variable is not set"**

   - Ensure you've added the VERCEL_AI_GATEWAY_KEY in Coolify environment variables
   - Redeploy after adding variables

2. **"Authentication failed" (Odoo)**

   - Verify ODOO_URL is correct and accessible
   - Check ODOO_DB name matches exactly
   - Verify username and password are correct
   - Test Odoo API access manually

3. **"ai_connected": false**

   - Verify your Vercel AI Gateway API key is valid
   - Check if you have access to Claude models in your Vercel AI Gateway
   - Ensure there are no API quota issues
   - Verify the gateway is properly configured

4. **"odoo_connected": false**
   - Check if Odoo is running
   - Verify network connectivity from Coolify to Odoo
   - Check firewall rules
   - Verify XML-RPC is enabled in Odoo

### Viewing Logs

In Coolify:

1. Go to your service
2. Click on **"Logs"**
3. View real-time application logs

Look for:

- Connection test results on startup
- API request/response logs
- Error messages

### Testing Odoo Connectivity

You can test if your Odoo instance is accessible:

```bash
curl -X POST http://your-odoo-url:8069/xmlrpc/2/common \
  -H "Content-Type: text/xml" \
  -d '<?xml version="1.0"?>
<methodCall>
  <methodName>version</methodName>
</methodCall>'
```

## Security Recommendations

1. **Use HTTPS**: Enable SSL in Coolify for your AI Agent domain
2. **Add Authentication**: Consider adding API key authentication to the AI Agent
3. **Restrict Access**: Use Coolify's built-in access controls or add a reverse proxy with authentication
4. **Environment Variables**: Never commit API keys or passwords to your repository
5. **Use Odoo Service Account**: Create a dedicated Odoo user for the AI Agent with minimum required permissions

## Updating the Service

To update your AI Agent:

1. Push changes to your Git repository
2. In Coolify, click **"Redeploy"**
3. Or enable automatic deployments on push

## Need Help?

- Check the application logs in Coolify
- Verify all environment variables are set correctly
- Test each component (Gemini API, Odoo connection) individually using the `/ping` endpoint
- Ensure your Odoo instance is accessible from the Coolify server

## Next Steps

Once deployed, you can:

- Integrate with your existing n8n workflow
- Add custom endpoints for specific operations
- Implement caching for better performance
- Add authentication and rate limiting
- Monitor usage and costs
