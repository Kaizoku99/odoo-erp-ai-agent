# Odoo ERP AI Agent

An AI-powered assistant for Odoo ERP that translates natural language queries into Odoo operations using Google Gemini AI.

## 🎯 What This Does

This AI Agent acts as an intelligent bridge between natural language and your Odoo ERP system. It can:

- Answer questions about your business data (sales, inventory, customers, etc.)
- Create, update, and delete records in Odoo
- Provide insights and analytics
- Integrate seamlessly with automation tools like n8n

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│    n8n      │─────▶│  AI Agent    │─────▶│    Odoo     │
│  Workflow   │      │  (Coolify)   │      │  Instance   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │Google Gemini │
                     │     API      │
                     └──────────────┘
```

## 🚀 Quick Start - Deploy to Coolify

The AI Agent can be deployed as a standalone service to Coolify and connected to any Odoo instance.

**See [COOLIFY_DEPLOYMENT.md](./ai_agent/COOLIFY_DEPLOYMENT.md) for detailed deployment instructions.**

### Prerequisites

- Coolify account
- Existing Odoo instance (local, cloud, or hosted)
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Quick Setup

1. Push this repository to your Git provider
2. Create a new service in Coolify from your repository
3. Set the Dockerfile path to `ai_agent/Dockerfile`
4. Add environment variables (see below)
5. Deploy!

### Required Environment Variables

```env
ODOO_URL=http://your-odoo-server:8069
ODOO_DB=your_database_name
ODOO_USERNAME=your_username@email.com
ODOO_PASSWORD=your_password
GEMINI_API_KEY=your_gemini_api_key
```

## 📡 API Endpoints

### Health Check
```bash
GET /ping
```

Response:
```json
{
  "status": "ok",
  "gemini_connected": true,
  "odoo_connected": true
}
```

### Chat with AI Agent
```bash
POST /chat
Content-Type: application/json

{
  "message": "How many open sales orders do we have?",
  "context": {},
  "conversation_history": []
}
```

Response:
```json
{
  "response": "You currently have 15 open sales orders with a total value of $47,320..."
}
```

## 🔧 Local Development with Docker

If you want to run everything locally (Odoo + AI Agent):

### Prerequisites
- Docker and docker-compose installed
- WSL (for Windows users)

### Installation Steps

1. Update and install required packages (WSL/Linux):
```bash
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl enable --now docker
```

2. Configure Docker permissions:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Server Management

Start all services:
```bash
docker-compose up -d
```

Stop services:
```bash
docker-compose down
```

Rebuild AI Agent:
```bash
docker-compose build ai_agent
```

Complete reset (deletes database):
```bash
docker-compose down -v
```

## 🔌 n8n Integration

Once deployed, integrate with n8n for powerful automation workflows with conversation memory!

### Quick Start

We provide ready-to-use n8n workflow templates:

1. **WhatsApp Bot with Memory** ⭐ - Smart conversations with PostgreSQL history (Recommended)
2. **WhatsApp Bot (Simple)** - Basic Q&A without memory
3. **Simple Test Webhook** - Test your AI agent with HTTP requests
4. **Original Complex** - Advanced multi-tool workflow

**📖 See [N8N_INTEGRATION_GUIDE.md](./N8N_INTEGRATION_GUIDE.md) for complete setup instructions**

**💬 See [CHAT_MEMORY_SETUP.md](./CHAT_MEMORY_SETUP.md) for conversation memory setup**

**📁 Browse workflow templates in [n8n_workflows/](./n8n_workflows/)**

### Quick Example

**HTTP Request Node Configuration:**
- Method: `POST`
- URL: `http://your-coolify-agent.sslip.io/chat`
- Body:
```json
{
  "message": "{{ $json.question }}",
  "conversation_history": []
}
```

**Example Questions:**
- "How many sales orders do we have this month?"
- "Show me low stock items"
- "Create a new lead for Acme Corp"
- "What's our total revenue this quarter?"
- "List all employees in the Sales department"
- "What vehicles are in our fleet?"

## 🛠️ Configuration

The AI Agent uses Google Gemini (`gemini-pro` model) by default. You can modify the model or add additional features in `ai_agent/app.py`.

### Supported Odoo Modules

The AI Agent automatically detects and works with installed modules:
- ✅ **Sales** - Orders, customers, sales teams
- ✅ **Inventory** - Products, stock levels, categories
- ✅ **Manufacturing** - BOMs, work orders, production
- ✅ **Purchasing** - Purchase orders, vendors, requisitions
- ✅ **Accounting** - Invoices, payments, journals
- ✅ **CRM** - Leads, opportunities, activities
- ✅ **HR/Employees** - Staff, departments, jobs
- ✅ **Payroll** - Payslips, salary structures
- ✅ **Attendances** - Check-ins, working hours
- ✅ **Fleet** - Vehicles, models, drivers
- ✅ **Expenses** - Employee expenses, reimbursements
- ✅ **Calendar** - Events, meetings, schedules
- ✅ **Contacts** - All partners (customers & suppliers)
- ✅ **Point of Sale** - POS orders, sessions
- ✅ **Companies & Users** - System information

*Fetches up to 100 records per module to optimize performance*

## 🔒 Security Recommendations

1. **Use HTTPS**: Enable SSL in Coolify
2. **Secure Credentials**: Never commit `.env` files
3. **API Authentication**: Add authentication to your endpoints (optional)
4. **Minimum Permissions**: Use a dedicated Odoo user with only required permissions
5. **Rate Limiting**: Implement rate limiting for production use

## 📝 Example Use Cases

1. **Sales Dashboard Updates**: "What are today's sales totals?"
2. **Inventory Alerts**: "Which products need reordering?"
3. **Customer Insights**: "Show me top 5 customers by revenue"
4. **Lead Management**: "Create a new lead for Company X"
5. **Financial Reports**: "What's our accounts receivable total?"

## 🆘 Troubleshooting

### Gemini API Issues
- Verify API key is correct
- Check Google Cloud Console for API status
- Ensure Generative Language API is enabled

### Odoo Connection Issues
- Verify ODOO_URL is accessible from Coolify server
- Check database name (case-sensitive)
- Confirm user credentials are correct
- Verify XML-RPC is enabled in Odoo

### Check Logs
In Coolify: Go to your service → Logs → View real-time logs

## 📚 Documentation

- [📘 Coolify Deployment Guide](./ai_agent/COOLIFY_DEPLOYMENT.md) - Deploy AI Agent to Coolify
- [🔌 n8n Integration Guide](./N8N_INTEGRATION_GUIDE.md) - Connect with n8n workflows
- [📁 n8n Workflow Templates](./n8n_workflows/) - Ready-to-use workflow files
- [⚙️ Environment Variables Template](./ai_agent/.env.example) - Configuration reference

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

MIT License - feel free to use this in your projects!