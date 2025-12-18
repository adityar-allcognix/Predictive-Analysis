-- Migration: 006_add_customer_contact_info
-- Purpose: Add email and phone_number to customers table for authentication

BEGIN;

-- Add email and phone_number columns to customers table
ALTER TABLE customers
  ADD COLUMN IF NOT EXISTS email TEXT UNIQUE,
  ADD COLUMN IF NOT EXISTS phone_number TEXT;

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email) WHERE email IS NOT NULL;

-- Add some demo email addresses to existing customers
UPDATE customers SET email = 'rajesh.kumar@example.com', phone_number = '+91-9876543210' WHERE customer_id = 'CUST-IN-0001';
UPDATE customers SET email = 'priya.sharma@example.com', phone_number = '+91-9876543211' WHERE customer_id = 'CUST-IN-0002';
UPDATE customers SET email = 'amit.patel@example.com', phone_number = '+91-9876543212' WHERE customer_id = 'CUST-IN-0003';
UPDATE customers SET email = 'neha.singh@example.com', phone_number = '+91-9876543213' WHERE customer_id = 'CUST-IN-0004';
UPDATE customers SET email = 'vikram.desai@example.com', phone_number = '+91-9876543214' WHERE customer_id = 'CUST-IN-0005';
UPDATE customers SET email = 'anjali.reddy@example.com', phone_number = '+91-9876543215' WHERE customer_id = 'CUST-IN-0006';
UPDATE customers SET email = 'sanjay.mehta@example.com', phone_number = '+91-9876543216' WHERE customer_id = 'CUST-IN-0007';
UPDATE customers SET email = 'kavita.nair@example.com', phone_number = '+91-9876543217' WHERE customer_id = 'CUST-IN-0008';
UPDATE customers SET email = 'arjun.gupta@example.com', phone_number = '+91-9876543218' WHERE customer_id = 'CUST-IN-0009';
UPDATE customers SET email = 'pooja.iyer@example.com', phone_number = '+91-9876543219' WHERE customer_id = 'CUST-IN-0010';

-- Add demo account with known credentials for testing
UPDATE customers SET email = 'demo@omnineura.com', phone_number = '+91-9999999999', full_name = 'Demo User' 
WHERE customer_id = 'CUST-IN-0001';

COMMIT;
