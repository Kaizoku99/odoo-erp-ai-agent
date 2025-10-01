from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import os
from dotenv import load_dotenv
import xmlrpc.client
import google.generativeai as genai
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8069"],  # Odoo frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Odoo connection settings
ODOO_URL = os.getenv("ODOO_URL", "http://web:8069")
ODOO_DB = os.getenv("ODOO_DB", "HISEY")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "cjhisey@gmail.com")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "odoo")

# Google Gemini settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

class ChatMessage(BaseModel):
    message: str
    context: Optional[dict] = None
    conversation_history: Optional[List[dict]] = None

class DatabaseOperation(BaseModel):
    model: str
    method: str
    args: List[Any]
    kwargs: Dict[str, Any] = {}

def connect_to_odoo():
    """Establish connection to Odoo instance"""
    try:
        logger.info(f"Connecting to Odoo at {ODOO_URL} with database {ODOO_DB}")
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        if not uid:
            raise Exception("Authentication failed. Please check your credentials and database name.")
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        logger.info("Successfully connected to Odoo")
        return uid, models
    except Exception as e:
        logger.error(f"Error connecting to Odoo: {str(e)}")
        raise

def get_odoo_context(limit_records=10):
    """Get current context from Odoo with limited records to reduce token usage"""
    try:
        logger.info("Connecting to Odoo...")
        # Connect to Odoo
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        
        logger.info(f"Fetching data (limited to {limit_records} records per query)...")
        context = {}
        
        # Check which modules are installed
        installed_modules = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'ir.module.module', 'search_read',
            [[['state', '=', 'installed']]],
            {'fields': ['name']})
        installed_module_names = [m['name'] for m in installed_modules]
        logger.info(f"Installed modules: {installed_module_names}")
        
        # Define module-specific data fetchers
        module_fetchers = {
            'stock': {
                'name': 'inventory',
                'fetch': lambda: {
                    'products': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'product.product', 'search_read',
                        [[['type', '=', 'product']]],
                        {'fields': ['name', 'qty_available', 'virtual_available', 'standard_price'], 'limit': limit_records}),
                    'categories': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'product.category', 'search_read',
                        [[]],
                        {'fields': ['name', 'parent_id'], 'limit': limit_records}),
                }
            },
            'mrp': {
                'name': 'manufacturing',
                'fetch': lambda: {
                    'boms': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'mrp.bom', 'search_read',
                        [[]],
                        {'fields': ['product_tmpl_id', 'product_qty', 'code'], 'limit': limit_records}),
                    'workcenters': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'mrp.workcenter', 'search_read',
                        [[]],
                        {'fields': ['name', 'resource_calendar_id', 'time_efficiency'], 'limit': limit_records}),
                    'production_orders': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'mrp.production', 'search_read',
                        [[['state', 'in', ['draft', 'confirmed', 'progress']]]],
                        {'fields': ['name', 'product_id', 'product_qty', 'state'], 'limit': limit_records}),
                }
            },
            'sale': {
                'name': 'sales',
                'fetch': lambda: {
                    'orders': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'sale.order', 'search_read',
                        [[['state', 'in', ['draft', 'sent', 'sale']]]],
                        {'fields': ['name', 'partner_id', 'amount_total', 'state', 'date_order'], 'limit': limit_records}),
                    'order_lines': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'sale.order.line', 'search_read',
                        [[['order_id.state', 'in', ['draft', 'sent', 'sale']]]],
                        {'fields': ['order_id', 'product_id', 'product_uom_qty', 'price_unit', 'price_subtotal'], 'limit': limit_records}),
                    'customers': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'res.partner', 'search_read',
                        [[['customer_rank', '>', 0]]],
                        {'fields': ['name', 'email', 'phone', 'street', 'city', 'country_id'], 'limit': limit_records}),
                }
            },
            'purchase': {
                'name': 'purchasing',
                'fetch': lambda: {
                    'orders': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'purchase.order', 'search_read',
                        [[['state', 'in', ['draft', 'sent', 'purchase']]]],
                        {'fields': ['name', 'partner_id', 'amount_total', 'state', 'date_order', 'date_planned'], 'limit': limit_records}),
                    'order_lines': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'purchase.order.line', 'search_read',
                        [[['order_id.state', 'in', ['draft', 'sent', 'purchase']]]],
                        {'fields': ['order_id', 'product_id', 'product_qty', 'price_unit', 'price_subtotal'], 'limit': limit_records}),
                    'suppliers': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'res.partner', 'search_read',
                        [[['supplier_rank', '>', 0]]],
                        {'fields': ['name', 'email', 'phone', 'street', 'city', 'country_id'], 'limit': limit_records}),
                }
            },
            'account': {
                'name': 'accounting',
                'fetch': lambda: {
                    'invoices': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'account.move', 'search_read',
                        [[['move_type', 'in', ['out_invoice', 'in_invoice']], ['state', '!=', 'cancel']]],
                        {'fields': ['name', 'partner_id', 'amount_total', 'state', 'invoice_date', 'invoice_date_due', 'payment_state'], 'limit': limit_records}),
                    'invoice_lines': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'account.move.line', 'search_read',
                        [[['move_id.move_type', 'in', ['out_invoice', 'in_invoice']], ['move_id.state', '!=', 'cancel']]],
                        {'fields': ['move_id', 'product_id', 'quantity', 'price_unit', 'price_subtotal'], 'limit': limit_records}),
                    'payments': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'account.payment', 'search_read',
                        [[['state', '!=', 'cancel']]],
                        {'fields': ['name', 'partner_id', 'amount', 'payment_type', 'date', 'state'], 'limit': limit_records}),
                }
            },
            'crm': {
                'name': 'crm',
                'fetch': lambda: {
                    'leads': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'crm.lead', 'search_read',
                        [[['type', '=', 'lead']]],
                        {'fields': ['name', 'partner_id', 'email_from', 'phone', 'stage_id', 'probability', 'expected_revenue', 'create_date'], 'limit': limit_records}),
                    'opportunities': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'crm.lead', 'search_read',
                        [[['type', '=', 'opportunity']]],
                        {'fields': ['name', 'partner_id', 'email_from', 'phone', 'stage_id', 'probability', 'expected_revenue', 'create_date'], 'limit': limit_records}),
                    'activities': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'mail.activity', 'search_read',
                        [[['res_model', '=', 'crm.lead']]],
                        {'fields': ['res_id', 'activity_type_id', 'summary', 'date_deadline', 'user_id', 'state'], 'limit': limit_records}),
                    'stages': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'crm.stage', 'search_read',
                        [[]],
                        {'fields': ['name', 'sequence', 'is_won'], 'limit': limit_records}),
                }
            },
            'hr': {
                'name': 'employees',
                'fetch': lambda: {
                    'employees': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'hr.employee', 'search_read',
                        [[]],
                        {'fields': ['name', 'job_id', 'department_id', 'work_email', 'work_phone', 'company_id'], 'limit': limit_records}),
                    'departments': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'hr.department', 'search_read',
                        [[]],
                        {'fields': ['name', 'manager_id', 'parent_id', 'company_id'], 'limit': limit_records}),
                    'jobs': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'hr.job', 'search_read',
                        [[]],
                        {'fields': ['name', 'department_id', 'no_of_employee', 'state'], 'limit': limit_records}),
                }
            },
            'hr_payroll': {
                'name': 'payroll',
                'fetch': lambda: {
                    'payslips': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'hr.payslip', 'search_read',
                        [[['state', 'in', ['draft', 'done']]]],
                        {'fields': ['name', 'employee_id', 'date_from', 'date_to', 'state', 'company_id'], 'limit': limit_records}),
                    'structures': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'hr.payroll.structure', 'search_read',
                        [[]],
                        {'fields': ['name', 'company_id'], 'limit': limit_records}),
                }
            },
            'hr_attendance': {
                'name': 'attendances',
                'fetch': lambda: {
                    'attendances': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'hr.attendance', 'search_read',
                        [[]],
                        {'fields': ['employee_id', 'check_in', 'check_out', 'worked_hours'], 'limit': limit_records}),
                }
            },
            'fleet': {
                'name': 'fleet',
                'fetch': lambda: {
                    'vehicles': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'fleet.vehicle', 'search_read',
                        [[]],
                        {'fields': ['name', 'model_id', 'driver_id', 'license_plate', 'state_id', 'company_id'], 'limit': limit_records}),
                    'vehicle_models': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'fleet.vehicle.model', 'search_read',
                        [[]],
                        {'fields': ['name', 'brand_id', 'vehicle_type'], 'limit': limit_records}),
                }
            },
            'hr_expense': {
                'name': 'expenses',
                'fetch': lambda: {
                    'expenses': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'hr.expense', 'search_read',
                        [[['state', 'in', ['draft', 'reported', 'approved', 'done']]]],
                        {'fields': ['name', 'employee_id', 'product_id', 'total_amount', 'state', 'date'], 'limit': limit_records}),
                    'expense_sheets': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'hr.expense.sheet', 'search_read',
                        [[['state', 'in', ['draft', 'submit', 'approve', 'post', 'done']]]],
                        {'fields': ['name', 'employee_id', 'total_amount', 'state', 'accounting_date'], 'limit': limit_records}),
                }
            },
            'calendar': {
                'name': 'calendar',
                'fetch': lambda: {
                    'events': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'calendar.event', 'search_read',
                        [[]],
                        {'fields': ['name', 'start', 'stop', 'allday', 'location', 'description', 'partner_ids'], 'limit': limit_records}),
                }
            },
            'contacts': {
                'name': 'contacts',
                'fetch': lambda: {
                    'contacts': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'res.partner', 'search_read',
                        [[]],
                        {'fields': ['name', 'email', 'phone', 'mobile', 'street', 'city', 'country_id', 'company_type', 'is_company'], 'limit': limit_records}),
                }
            },
            'point_of_sale': {
                'name': 'pos',
                'fetch': lambda: {
                    'orders': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'pos.order', 'search_read',
                        [[['state', 'in', ['draft', 'paid', 'done', 'invoiced']]]],
                        {'fields': ['name', 'partner_id', 'date_order', 'amount_total', 'state', 'session_id'], 'limit': limit_records}),
                    'sessions': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'pos.session', 'search_read',
                        [[['state', 'in', ['opening_control', 'opened', 'closing_control']]]],
                        {'fields': ['name', 'user_id', 'start_at', 'stop_at', 'state', 'config_id'], 'limit': limit_records}),
                }
            },
            'base': {
                'name': 'companies',
                'fetch': lambda: {
                    'companies': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'res.company', 'search_read',
                        [[]],
                        {'fields': ['name', 'email', 'phone', 'website', 'street', 'city', 'country_id', 'currency_id'], 'limit': limit_records}),
                    'users': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'res.users', 'search_read',
                        [[]],
                        {'fields': ['name', 'login', 'email', 'company_id', 'active'], 'limit': limit_records}),
                }
            }
        }
        
        # Fetch data for each installed module
        # Note: 'base' is always installed, so companies/users will always be available
        for module_name, fetcher in module_fetchers.items():
            # Special handling for base module (always present)
            if module_name == 'base':
                try:
                    logger.info(f"Fetching data for base module (companies/users)")
                    context[fetcher['name']] = fetcher['fetch']()
                    logger.info(f"Successfully fetched base module data")
                except Exception as e:
                    logger.error(f"Error fetching base module data: {str(e)}")
                    continue
            # For contacts, always try to fetch (res.partner is a base model)
            elif module_name == 'contacts':
                try:
                    logger.info(f"Fetching contacts data")
                    context[fetcher['name']] = fetcher['fetch']()
                    logger.info(f"Successfully fetched contacts data")
                except Exception as e:
                    logger.error(f"Error fetching contacts data: {str(e)}")
                    continue
            # For calendar, always try (calendar.event is a base model)
            elif module_name == 'calendar':
                try:
                    logger.info(f"Fetching calendar data")
                    context[fetcher['name']] = fetcher['fetch']()
                    logger.info(f"Successfully fetched calendar data")
                except Exception as e:
                    logger.error(f"Error fetching calendar data: {str(e)}")
                    continue
            # For other modules, check if installed
            elif module_name in installed_module_names:
                try:
                    logger.info(f"Fetching data for module: {module_name}")
                    context[fetcher['name']] = fetcher['fetch']()
                    logger.info(f"Successfully fetched data for {module_name}")
                except Exception as e:
                    logger.error(f"Error fetching data for module {module_name}: {str(e)}")
                    logger.error(f"Error type: {type(e)}")
                    logger.error(f"Error args: {e.args}")
                    # Continue with other modules even if one fails
                    continue
        
        logger.info(f"Retrieved context: {context}")
        return context
    except Exception as e:
        logger.error(f"Error getting Odoo context: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error args: {e.args}")
        return {}

def test_gemini_connection():
    """Test the connection to Google Gemini API"""
    try:
        logger.info("Testing Google Gemini API connection...")
        logger.info(f"API Key length: {len(GEMINI_API_KEY)}")
        logger.info(f"API Key prefix: {GEMINI_API_KEY[:10]}...")
        
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
        response = model.generate_content("Hello, this is a test message.")
        logger.info("Google Gemini API connection successful!")
        return True
    except Exception as e:
        logger.error(f"Google Gemini API connection failed: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error args: {e.args}")
        return False

def execute_database_operation(operation: DatabaseOperation):
    """Execute a database operation safely"""
    try:
        logger.info(f"Executing database operation: {operation.model}.{operation.method}")
        logger.info(f"Args: {operation.args}")
        logger.info(f"Kwargs: {operation.kwargs}")
        
        # Connect to Odoo
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        
        # Execute the operation
        result = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            operation.model,
            operation.method,
            operation.args,
            operation.kwargs
        )
        
        logger.info(f"Operation successful. Result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error executing database operation: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error args: {e.args}")
        raise

def process_with_llm(message: str, context: dict, conversation_history: List[dict] = None):
    """Process the message with Google Gemini and return a response"""
    try:
        logger.info("Initializing Google Gemini model...")
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
        
        # Convert context to a readable format
        context_str = ""
        if context:
            for section, data in context.items():
                context_str += f"\n{section.upper()}:\n"
                for key, items in data.items():
                    context_str += f"\n{key}:\n"
                    if isinstance(items, list):
                        for item in items:
                            context_str += f"- {item}\n"
                    else:
                        context_str += f"- {items}\n"
        
        logger.info(f"Formatted context being sent to LLM: {context_str}")
        
        system_prompt = f"""You are an AI assistant for an Odoo ERP system. 
        You have access to the following context about the system:
        {context_str}
        
        Your task is to help users with their ERP operations. You can:
        1. Answer questions about inventory levels, products, and categories
        2. Help with manufacturing processes, BOMs, and work centers
        3. Provide information about sales orders and customers
        4. Assist with purchase orders and supplier information
        5. Help with accounting, invoices, and payments
        6. Provide information about CRM leads, opportunities, and activities
        7. Answer questions about employees, departments, and job positions
        8. Help with payroll, payslips, and salary structures
        9. Track employee attendance and working hours
        10. Manage fleet vehicles and vehicle models
        11. Process and track employee expenses
        12. View and manage calendar events and meetings
        13. Access contact information for all partners
        14. Help with Point of Sale orders and sessions
        15. Provide information about companies and system users
        16. Provide insights about the data and suggest actions
        17. Analyze relationships between different aspects of the business
        18. Make changes to the database when requested
        
        When making changes to the database, you should:
        1. First confirm the change with the user
        2. Use the appropriate model and method
        3. Provide clear feedback about what was changed
        
        Available write operations:
        - create: Create new records
        - write: Update existing records
        - unlink: Delete records
        
        Example operations:
        - Create a new lead: DATABASE_OPERATION:{{"model": "crm.lead", "method": "create", "args": [[{{"name": "New Lead", "partner_id": 1}}]]}}
        - Update a lead: DATABASE_OPERATION:{{"model": "crm.lead", "method": "write", "args": [[1], {{"name": "Updated Lead"}}]]}}
        - Delete a lead: DATABASE_OPERATION:{{"model": "crm.lead", "method": "unlink", "args": [[1]]}}
        
        Always be professional and precise in your responses. When providing information:
        - Use specific numbers and data from the context when available
        - Explain your reasoning when making suggestions
        - Highlight any potential issues or concerns
        - Suggest next steps when appropriate
        
        IMPORTANT: Maintain context from previous messages in the conversation. If the user refers to something 
        mentioned earlier (like a specific lead, customer, or order), use that information to provide relevant responses."""
        
        # Prepare the full prompt with conversation history
        full_prompt = system_prompt + "\n\n"
        if conversation_history:
            for msg in conversation_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                full_prompt += f"{role.upper()}: {content}\n\n"
        full_prompt += f"USER: {message}\n\nASSISTANT:"
        
        logger.info("Sending request to Google Gemini API...")
        response = model.generate_content(full_prompt)
        logger.info("Received response from Google Gemini API")
        return response.text
    except Exception as e:
        logger.error(f"Error in LLM processing: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error args: {e.args}")
        
        # Check if it's a rate limit error
        if "429" in str(e) or "quota" in str(e).lower():
            return "I'm currently experiencing high usage. Please wait a moment and try again. (Rate limit reached)"
        
        raise

@app.get("/ping")
async def ping():
    """Test endpoint to verify service health"""
    try:
        # Test Google Gemini API connection
        gemini_connected = test_gemini_connection()
        
        # Test Odoo connection
        try:
            connect_to_odoo()
            odoo_connected = True
        except Exception as e:
            logger.error(f"Odoo connection failed: {str(e)}")
            odoo_connected = False
        
        return {
            "status": "ok",
            "gemini_connected": gemini_connected,
            "odoo_connected": odoo_connected
        }
    except Exception as e:
        logger.error(f"Ping test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(message: ChatMessage):
    try:
        logger.info(f"Received chat message: {message.message}")
        logger.info(f"Message context: {message.context}")
        logger.info(f"Conversation history: {message.conversation_history}")
        
        # Get current Odoo context with limited records (500 instead of all)
        logger.info("Fetching Odoo context...")
        context = get_odoo_context(limit_records=500)
        logger.info(f"Retrieved Odoo context: {context}")
        
        # Process the message with LLM
        logger.info("Processing message with LLM...")
        response = process_with_llm(message.message, context, message.conversation_history)
        
        # Check if the response contains a database operation
        try:
            if "DATABASE_OPERATION:" in response:
                # Extract the JSON part after DATABASE_OPERATION:
                operation_str = response.split("DATABASE_OPERATION:")[1].strip()
                # Remove any text after the JSON (in case there's additional text)
                operation_str = operation_str.split('\n')[0].strip()
                logger.info(f"Attempting to parse operation: {operation_str}")
                
                try:
                    operation = DatabaseOperation(**json.loads(operation_str))
                    result = execute_database_operation(operation)
                    response = response.split("DATABASE_OPERATION:")[0] + f"\nOperation successful: {result}"
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error: {str(e)}")
                    response = f"Error in database operation format. Please ensure the operation is valid JSON. Error: {str(e)}"
                except Exception as e:
                    logger.error(f"Error executing database operation: {str(e)}")
                    response = f"Error executing database operation: {str(e)}"
        except Exception as e:
            logger.error(f"Error processing database operation: {str(e)}")
            response = f"Error processing database operation: {str(e)}"
        
        return {"response": response}
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error args: {e.args}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 