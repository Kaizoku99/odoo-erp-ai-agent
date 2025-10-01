# 💬 Chat Memory Setup Guide

This guide explains how to set up persistent conversation memory for your WhatsApp AI agent, enabling back-and-forth conversations with context retention.

---

## 📋 Overview

The memory-enabled workflow stores conversation history in PostgreSQL, allowing the AI agent to:
- **Remember previous messages** in the conversation
- **Maintain context** across multiple interactions
- **Provide relevant follow-up responses** based on chat history
- **Handle complex multi-turn conversations**

### Workflow Flow:
```
WhatsApp Message → Extract Message → Get Chat History (PostgreSQL) 
→ Build Context → Call AI Agent (with history) → Save to History (PostgreSQL)
→ Format Response → Send WhatsApp Reply → Cleanup Old Messages
```

---

## 🗄️ Database Setup

### Step 1: Set Up PostgreSQL

You need a PostgreSQL database. Choose one option:

#### Option A: Use Existing PostgreSQL
If you already have PostgreSQL running, skip to Step 2.

#### Option B: Deploy PostgreSQL on Coolify
1. Go to your Coolify dashboard
2. Click **+ Add Resource** → **Database**
3. Select **PostgreSQL**
4. Configure:
   - **Database Name**: `n8n_chat_memory`
   - **Username**: `n8n_user`
   - **Password**: (generate a strong password)
5. Click **Create**
6. Note the connection details:
   ```
   Host: your-postgres-host
   Port: 5432
   Database: n8n_chat_memory
   Username: n8n_user
   Password: your-password
   ```

#### Option C: Use Supabase (Free)
1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Go to **Settings** → **Database**
4. Copy the **Connection String** (Transaction mode)
5. Use these details in n8n

---

### Step 2: Create the Chat History Table

The workflow will automatically create the table on first run, but you can manually create it:

```sql
CREATE TABLE IF NOT EXISTS chat_history (
  id SERIAL PRIMARY KEY,
  session_key VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_session_key ON chat_history(session_key);
CREATE INDEX idx_created_at ON chat_history(created_at);
```

**Table Structure:**
- `id`: Auto-incrementing primary key
- `session_key`: Unique identifier for each WhatsApp conversation (format: `phone_instance`)
- `role`: Either `user` or `assistant`
- `content`: The actual message text
- `created_at`: Timestamp of the message

---

## 🔧 n8n Setup

### Step 1: Configure PostgreSQL Credentials in n8n

1. Open your n8n instance
2. Go to **Credentials** (gear icon in top right)
3. Click **+ Add Credential**
4. Select **Postgres**
5. Fill in your database details:
   ```
   Host: your-postgres-host
   Port: 5432
   Database: n8n_chat_memory
   User: n8n_user
   Password: your-password
   SSL: (enable if required)
   ```
6. Click **Save**
7. Note the credential name (you'll need it in the workflow)

---

### Step 2: Import the Memory-Enabled Workflow

1. Download `n8n_workflows/whatsapp_with_memory.json`
2. In n8n, click **Import from File**
3. Select the downloaded JSON file
4. The workflow will open in the editor

---

### Step 3: Configure Workflow Nodes

#### 1. **Get Chat History** Node
- Click the node
- Select your PostgreSQL credential
- The query will automatically:
  - Create the table if it doesn't exist
  - Retrieve last 10 messages for the session
  - Order by most recent first

#### 2. **Save to History** Node
- Click the node
- Select the same PostgreSQL credential
- This stores both:
  - User's message with role `user`
  - AI's response with role `assistant`

#### 3. **Cleanup Old Messages** Node
- Click the node
- Select the same PostgreSQL credential
- Automatically deletes messages older than 30 days
- Keeps your database clean

#### 4. **Evolution API Credentials**
- Click **Send WhatsApp Reply** node
- Add your Evolution API credentials:
  - **API URL**: Your Evolution API instance URL
  - **API Key**: Your Evolution API key

---

### Step 4: Activate the Workflow

1. Copy the webhook URL from **WhatsApp Webhook** node
2. Configure this webhook in your Evolution API:
   - Go to Evolution API settings
   - Add webhook URL for **message events**
   - Enable **incoming message notifications**
3. Click **Active** toggle in n8n to activate the workflow

---

## 🧪 Testing

### Test Conversation Flow:

Send these messages in sequence from WhatsApp:

```
1️⃣ User: "How many sales orders do we have?"
   AI: "We currently have 5 sales orders..."

2️⃣ User: "Show me the top 3"
   AI: (remembers previous context about sales orders)
   "Here are the top 3 sales orders: ..."

3️⃣ User: "What's the status of the first one?"
   AI: (remembers "first one" refers to the list just shown)
   "The status of SO001 is: ..."

4️⃣ User: "Can you update it to confirmed?"
   AI: (remembers which order you're talking about)
   "I'll update SO001 to confirmed status..."
```

### Verify Database Storage:

Check if messages are being saved:

```sql
-- View recent conversations
SELECT session_key, role, content, created_at
FROM chat_history
ORDER BY created_at DESC
LIMIT 20;

-- Check specific conversation
SELECT role, content, created_at
FROM chat_history
WHERE session_key = '5511999999999_default'
ORDER BY created_at DESC;
```

---

## ⚙️ Configuration Options

### Adjust Memory Length

By default, the AI sees the **last 10 messages**. To change this:

1. Open **Get Chat History** node
2. Edit the SQL query
3. Change `LIMIT 10` to your desired number:
   ```sql
   LIMIT 20  -- Shows last 20 messages (10 exchanges)
   LIMIT 50  -- Shows last 50 messages (25 exchanges)
   ```

**Note:** More messages = more tokens sent to AI = higher costs and slower responses.

### Adjust Cleanup Period

By default, messages older than **30 days** are deleted. To change:

1. Open **Cleanup Old Messages** node
2. Edit the interval:
   ```sql
   -- Keep for 7 days
   WHERE created_at < NOW() - INTERVAL '7 days'
   
   -- Keep for 90 days
   WHERE created_at < NOW() - INTERVAL '90 days'
   
   -- Keep forever (not recommended)
   -- Just disable the Cleanup node
   ```

### Multiple Customers

The workflow automatically handles multiple customers:
- Each WhatsApp number gets a unique `session_key`
- Conversations are completely isolated
- No cross-contamination between customers

**Session Key Format:**
```
{phone_number}_{instance_name}

Examples:
5511999999999_default
5521888888888_sales_bot
```

---

## 🔍 Troubleshooting

### Problem: AI doesn't remember previous messages

**Check:**
1. Is the **Get Chat History** node executing successfully?
   - Check n8n execution logs
   - Verify PostgreSQL credentials are correct

2. Is data being saved to the database?
   ```sql
   SELECT COUNT(*) FROM chat_history;
   ```
   - If 0, check **Save to History** node

3. Is the session key consistent?
   - Check n8n execution logs for `session_key` value
   - Should be same for all messages from same user

### Problem: Database connection fails

**Solutions:**
1. **Verify credentials** in n8n
2. **Check PostgreSQL is running**:
   ```bash
   # If using Coolify
   Check Coolify dashboard → Database status
   
   # If using Supabase
   Check Supabase dashboard → Project status
   ```
3. **Test connection** from n8n:
   - Edit PostgreSQL credential
   - Click **Test**
   - Should show "Connection successful"

### Problem: Messages not appearing in database

**Check SQL syntax:**
1. Open **Save to History** node
2. Click **Execute Node** to test
3. Check for SQL errors in execution log

**Common issue:** Special characters in messages
- Solution: The workflow uses `toJsonString` filter to escape special characters
- Verify this is present in the query: `{{ $json.message | toJsonString }}`

### Problem: Old messages not being deleted

**Check:**
1. Is **Cleanup Old Messages** node connected?
2. Is it being executed?
   - Look for it in execution logs
3. Are there messages older than 30 days?
   ```sql
   SELECT COUNT(*) FROM chat_history 
   WHERE created_at < NOW() - INTERVAL '30 days';
   ```

---

## 📊 Database Management

### View All Conversations

```sql
SELECT 
  session_key,
  COUNT(*) as message_count,
  MIN(created_at) as first_message,
  MAX(created_at) as last_message
FROM chat_history
GROUP BY session_key
ORDER BY last_message DESC;
```

### Export a Conversation

```sql
SELECT role, content, created_at
FROM chat_history
WHERE session_key = 'YOUR_SESSION_KEY'
ORDER BY created_at ASC;
```

### Clear All History (Reset)

```sql
-- Delete all messages
TRUNCATE TABLE chat_history;

-- Or delete specific conversation
DELETE FROM chat_history 
WHERE session_key = 'SPECIFIC_SESSION_KEY';
```

### Database Size Monitoring

```sql
-- Check table size
SELECT 
  pg_size_pretty(pg_total_relation_size('chat_history')) as total_size,
  COUNT(*) as row_count
FROM chat_history;

-- Check rows per session
SELECT 
  session_key,
  COUNT(*) as messages,
  pg_size_pretty(SUM(LENGTH(content))) as text_size
FROM chat_history
GROUP BY session_key
ORDER BY messages DESC;
```

---

## 🚀 Advanced Features

### Add User Metadata

Store additional information about conversations:

```sql
-- Add columns to track user details
ALTER TABLE chat_history
ADD COLUMN customer_name VARCHAR(255),
ADD COLUMN customer_phone VARCHAR(50);

-- Update workflow to save this data
-- Modify "Save to History" node to include:
INSERT INTO chat_history (
  session_key, role, content, customer_name, customer_phone
)
VALUES (
  '{{ $('Build Context').item.json.session_key }}',
  'user',
  {{ $('Build Context').item.json.message | toJsonString }},
  '{{ $('Build Context').item.json.customer_name }}',
  '{{ $('Build Context').item.json.customer_phone }}'
);
```

### Add Sentiment Analysis

Track conversation sentiment:

```sql
ALTER TABLE chat_history
ADD COLUMN sentiment VARCHAR(20);

-- Store sentiment from AI analysis
-- (requires adding sentiment detection to your AI prompt)
```

### Add Session Timeout

Clear inactive conversations:

```sql
-- Delete sessions inactive for 24 hours
DELETE FROM chat_history
WHERE session_key IN (
  SELECT DISTINCT session_key
  FROM chat_history
  GROUP BY session_key
  HAVING MAX(created_at) < NOW() - INTERVAL '24 hours'
);
```

---

## 📈 Performance Optimization

### Add More Indexes

For better query performance with large datasets:

```sql
-- Composite index for session + date queries
CREATE INDEX idx_session_created 
ON chat_history(session_key, created_at DESC);

-- Index for role-based queries
CREATE INDEX idx_role ON chat_history(role);
```

### Partition Large Tables

If you have millions of messages:

```sql
-- Create partitioned table (PostgreSQL 10+)
CREATE TABLE chat_history (
  id SERIAL,
  session_key VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE chat_history_2025_10 
  PARTITION OF chat_history
  FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
```

---

## 🔐 Security Best Practices

1. **Use SSL for database connections** (enable SSL in n8n credentials)
2. **Encrypt sensitive data** in messages if needed
3. **Set up database backups** (Coolify/Supabase have automatic backups)
4. **Limit database user permissions**:
   ```sql
   -- Create restricted user
   CREATE USER n8n_app WITH PASSWORD 'strong_password';
   GRANT SELECT, INSERT, DELETE ON chat_history TO n8n_app;
   GRANT USAGE, SELECT ON SEQUENCE chat_history_id_seq TO n8n_app;
   ```
5. **Monitor database access** through logs
6. **Implement GDPR compliance** (add data deletion endpoints)

---

## 🎯 Next Steps

- ✅ Set up PostgreSQL database
- ✅ Import memory-enabled workflow to n8n
- ✅ Configure database credentials
- ✅ Test conversation flow
- ✅ Monitor database growth
- 🔄 Optional: Add user metadata tracking
- 🔄 Optional: Implement session timeout
- 🔄 Optional: Add sentiment analysis

---

## 📚 Related Documentation

- [Main n8n Integration Guide](./N8N_INTEGRATION_GUIDE.md)
- [Workflow Comparison](./n8n_workflows/README.md)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [n8n Postgres Node](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.postgres/)

---

## 💡 Tips

1. **Start with 10 messages** in history - increase only if needed
2. **Monitor token usage** - more history = more tokens
3. **Test thoroughly** before production deployment
4. **Set up database backups** before going live
5. **Use indexes** for better performance with large datasets
6. **Clean up old data regularly** to keep database fast

Need help? Check the troubleshooting section or refer to the main integration guide!
