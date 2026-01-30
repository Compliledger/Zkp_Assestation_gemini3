-- ============================================
-- ZKPA Database Initialization Script
-- ============================================

-- Create database if not exists (run as postgres superuser)
-- CREATE DATABASE zkpa_dev;

-- Create user if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'zkpa_user') THEN
        CREATE ROLE zkpa_user WITH LOGIN PASSWORD 'zkpa_password';
    END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE zkpa_dev TO zkpa_user;

-- Connect to zkpa_dev and set up schema
\c zkpa_dev;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO zkpa_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO zkpa_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO zkpa_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO zkpa_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO zkpa_user;

-- ============================================
-- Tables will be created by Alembic migrations
-- Run: alembic upgrade head
-- ============================================
