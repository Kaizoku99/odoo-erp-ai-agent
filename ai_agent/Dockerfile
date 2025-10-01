FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Accept build arguments
ARG GEMINI_API_KEY
ARG ODOO_URL
ARG ODOO_DB
ARG ODOO_USERNAME
ARG ODOO_PASSWORD

# Set as environment variables for runtime
ENV GEMINI_API_KEY=${GEMINI_API_KEY}
ENV ODOO_URL=${ODOO_URL}
ENV ODOO_DB=${ODOO_DB}
ENV ODOO_USERNAME=${ODOO_USERNAME}
ENV ODOO_PASSWORD=${ODOO_PASSWORD}

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"] 