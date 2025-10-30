# Odoo AI Agent with Claude Haiku 4.5

A standalone FastAPI service that provides AI-powered assistance for Odoo ERP using Claude Haiku 4.5 via Vercel AI Gateway.

## Features

- 🤖 **Claude Haiku 4.5**: Fast, efficient AI responses using Anthropic's Claude Haiku 4.5 model
- 🔌 **Vercel AI Gateway**: Unified API access to multiple AI models with OpenAI-compatible endpoints
- 📊 **Odoo Integration**: Direct XML-RPC connection to Odoo for real-time data access
- 💬 **Conversation Memory**: Support for conversation history to maintain context
- 🔄 **Multi-Module Support**: Handles Sales, Inventory, Manufacturing, CRM, HR, Accounting, and more
- 🚀 **RESTful API**: Easy integration with n8n, webhooks, and other automation tools

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Client    │─────▶│  AI Agent    │─────▶│    Odoo     │
│ (n8n/API)   │      │  (FastAPI)   │      │  Instance   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │Vercel AI     │
                     │Gateway       │
                     │(Claude 4.5)  │
                     └──────────────┘
```

## Quick Start

### Prerequisites

1. **Odoo Instance**: Running Odoo instance (local or remote)
2. **Vercel AI Gateway Key**: Get from [Vercel AI Gateway](https://vercel.com/ai-gateway)
3. **Python 3.9+**: For local development

### Installation

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd ai_agent
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

5. **Run the application**
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

### Environment Variables

| Variable                | Description                    | Example                 |
| ----------------------- | ------------------------------ | ----------------------- |
| `ODOO_URL`              | Full URL to your Odoo instance | `http://localhost:8069` |
| `ODOO_DB`               | Odoo database name             | `my_database`           |
| `ODOO_USERNAME`         | Odoo username with API access  | `admin@example.com`     |
| `ODOO_PASSWORD`         | Odoo user password             | `your_password`         |
| `VERCEL_AI_GATEWAY_KEY` | Your Vercel AI Gateway API key | `vag_xxxxxxxxxxxxx`     |

## API Endpoints

### GET /ping

Health check endpoint to verify connections.

**Response:**

```json
{
  "status": "ok",
  "ai_connected": true,
  "ai_model": "anthropic/claude-haiku-4.5",
  "odoo_connected": true
}
```

### POST /chat

Main endpoint for AI-powered Odoo assistance.

**Request:**

```json
{
  "message": "How many active sales orders do we have?",
  "context": {},
  "conversation_history": [
    {
      "role": "user",
      "content": "Previous message"
    },
    {
      "role": "assistant",
      "content": "Previous response"
    }
  ]
}
```

**Response:**

```json
{
  "response": "Based on the current data, you have 15 active sales orders..."
}
```

## Why Claude Haiku 4.5?

- **Near-frontier performance** at a fraction of the cost
- **Fast response times** ideal for real-time applications
- **Context awareness** tracks context window throughout conversations
- **Extended thinking** capabilities for complex problem-solving
- **Cost-effective**: $1 per million input tokens, $5 per million output tokens

## Why Vercel AI Gateway?

- **Unified API** for multiple AI providers
- **OpenAI-compatible** endpoints for easy integration
- **Built-in monitoring** and usage analytics
- **Reliability** with automatic failover
- **Cost tracking** and optimization

## Docker Deployment

### Build the image

```bash
docker build -t odoo-ai-agent .
```

### Run the container

```bash
docker run -d \
  -p 8000:8000 \
  -e ODOO_URL=http://your-odoo:8069 \
  -e ODOO_DB=your_database \
  -e ODOO_USERNAME=your_username \
  -e ODOO_PASSWORD=your_password \
  -e VERCEL_AI_GATEWAY_KEY=your_api_key \
  --name odoo-ai-agent \
  odoo-ai-agent
```

## Deployment to Coolify

See [COOLIFY_DEPLOYMENT.md](./COOLIFY_DEPLOYMENT.md) for detailed deployment instructions.

## Usage Examples

### With cURL

```bash
# Check health
curl http://localhost:8000/ping

# Ask a question
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me the top 5 customers by revenue"
  }'

# With conversation history
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What about their recent orders?",
    "conversation_history": [
      {
        "role": "user",
        "content": "Show me the top 5 customers by revenue"
      },
      {
        "role": "assistant",
        "content": "Here are your top 5 customers..."
      }
    ]
  }'
```

### With n8n

1. Create an HTTP Request node
2. Set method to POST
3. Set URL to `https://your-ai-agent.coolify.app/chat`
4. Add header: `Content-Type: application/json`
5. Set body to:
   ```json
   {
     "message": "{{ $json.question }}",
     "context": {},
     "conversation_history": []
   }
   ```

### With Python

```python
import requests

url = "http://localhost:8000/chat"
payload = {
    "message": "How many products are in stock?",
    "context": {},
    "conversation_history": []
}

response = requests.post(url, json=payload)
print(response.json()["response"])
```

## Supported Odoo Modules

The AI agent can interact with the following Odoo modules:

- ✅ Sales (Orders, Customers)
- ✅ Inventory (Products, Stock Levels, Categories)
- ✅ Manufacturing (BOMs, Work Centers, Production Orders)
- ✅ Purchase (Purchase Orders, Suppliers)
- ✅ Accounting (Invoices, Payments)
- ✅ CRM (Leads, Opportunities, Activities)
- ✅ HR (Employees, Departments, Jobs)
- ✅ Payroll (Payslips, Salary Structures)
- ✅ Attendance (Check-ins, Work Hours)
- ✅ Fleet (Vehicles, Models)
- ✅ Expenses (Employee Expenses, Expense Sheets)
- ✅ Calendar (Events, Meetings)
- ✅ Contacts (Partners, Companies)
- ✅ Point of Sale (POS Orders, Sessions)

## Development

### Project Structure

```
ai_agent/
├── app.py                    # Main FastAPI application
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker configuration
├── .env.example            # Environment variables template
├── README.md               # This file
├── COOLIFY_DEPLOYMENT.md   # Deployment guide
└── templates/
    └── index.html          # Simple test UI
```

### Running Tests

```bash
# Test Odoo connection
python -c "from app import connect_to_odoo; connect_to_odoo()"

# Test AI Gateway connection
python -c "from app import test_ai_connection; test_ai_connection()"
```

### Adding New Features

1. Modify `app.py` to add new endpoints or functionality
2. Update `requirements.txt` if you add new dependencies
3. Test locally with `uvicorn app:app --reload`
4. Update documentation as needed

## Troubleshooting

### AI Gateway Connection Issues

- Verify your `VERCEL_AI_GATEWAY_KEY` is correct
- Check if you have access to Claude models in your Vercel account
- Monitor your API usage and quotas

### Odoo Connection Issues

- Ensure `ODOO_URL` is accessible from the AI agent
- Verify `ODOO_DB` name is correct (case-sensitive)
- Check that XML-RPC is enabled in Odoo
- Confirm user has appropriate permissions

### Rate Limiting

If you encounter rate limits:

- Implement caching for frequently accessed data
- Reduce the `limit_records` parameter in `get_odoo_context()`
- Consider upgrading your Vercel AI Gateway plan

## Performance Optimization

### Context Optimization

By default, the agent fetches up to 500 records per query. Adjust this in `app.py`:

```python
context = get_odoo_context(limit_records=100)  # Reduce for faster responses
```

### Caching

Consider implementing Redis caching for:

- Odoo context data (refresh every 5-10 minutes)
- Frequently asked questions
- Common database queries

## Security

- ✅ Never commit `.env` file with secrets
- ✅ Use environment variables for all credentials
- ✅ Implement API key authentication for production
- ✅ Use HTTPS in production (SSL/TLS)
- ✅ Create dedicated Odoo user with minimal required permissions
- ✅ Monitor API usage and set rate limits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions:

- Create an issue in the repository
- Check the [COOLIFY_DEPLOYMENT.md](./COOLIFY_DEPLOYMENT.md) for deployment help
- Review Vercel AI Gateway docs: https://vercel.com/docs/ai-gateway
- Review Claude documentation: https://docs.anthropic.com/

## Acknowledgments

- **Anthropic**: For Claude Haiku 4.5
- **Vercel**: For AI Gateway infrastructure
- **Odoo**: For the amazing ERP system
- **FastAPI**: For the excellent Python framework
