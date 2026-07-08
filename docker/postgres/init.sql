-- ==============================================================================
-- PostgreSQL Initialization Script
--
-- This script runs ONCE when the PostgreSQL container is first created.
-- It sets up any database-level extensions and configurations.
--
-- WHY uuid-ossp extension?
--   Our tables use UUID primary keys.
--   uuid_generate_v4() generates random UUIDs at the database level.
--   This allows PK generation without requiring application code.
--
-- Location: This file is mounted to:
--   /docker-entrypoint-initdb.d/init.sql
-- PostgreSQL automatically runs all .sql files in that directory on first start.
-- ==============================================================================

-- Enable UUID generation functions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable case-insensitive text (useful for email searches)
CREATE EXTENSION IF NOT EXISTS "citext";

-- Verify extensions are loaded
SELECT extname, extversion FROM pg_extension WHERE extname IN ('uuid-ossp', 'citext');
