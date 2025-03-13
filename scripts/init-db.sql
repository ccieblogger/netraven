-- NetRaven PostgreSQL initialization script
-- This script runs when the PostgreSQL container first starts

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schema if not exists (useful for multitenancy in the future)
CREATE SCHEMA IF NOT EXISTS netraven;

-- Set search path
SET search_path TO netraven, public;

-- Basic initialization complete
-- Tables will be created by SQLAlchemy on application startup 