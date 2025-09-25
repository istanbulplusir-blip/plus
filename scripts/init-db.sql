-- Istanbul Plus Database Initialization Script
-- This script sets up the initial database configuration

-- Create database if it doesn't exist (this will be handled by Docker)
-- CREATE DATABASE istanbulplus_db;

-- Set timezone
SET timezone = 'Asia/Tehran';

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Set default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO istanbulplus_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO istanbulplus_user;

-- Create indexes for better performance
-- These will be created after Django migrations, but we can prepare the database

-- Optimize PostgreSQL settings for Django
-- These settings will be applied at the database level
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET pg_stat_statements.track = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;
ALTER SYSTEM SET log_checkpoints = on;
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_lock_waits = on;

-- Create a function to clean up old sessions
CREATE OR REPLACE FUNCTION cleanup_old_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM django_session WHERE expire_date < NOW();
END;
$$ LANGUAGE plpgsql;

-- Create a function to clean up old OTP codes
CREATE OR REPLACE FUNCTION cleanup_old_otp_codes()
RETURNS void AS $$
BEGIN
    DELETE FROM users_otpcode WHERE created_at < NOW() - INTERVAL '1 hour';
END;
$$ LANGUAGE plpgsql;

-- Create a function to clean up old security logs
CREATE OR REPLACE FUNCTION cleanup_old_security_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM users_securitylog WHERE created_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions on cleanup functions
GRANT EXECUTE ON FUNCTION cleanup_old_sessions() TO istanbulplus_user;
GRANT EXECUTE ON FUNCTION cleanup_old_otp_codes() TO istanbulplus_user;
GRANT EXECUTE ON FUNCTION cleanup_old_security_logs() TO istanbulplus_user;

-- Create a view for monitoring database performance
CREATE OR REPLACE VIEW database_stats AS
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY tablename, attname;

-- Grant access to the monitoring view
GRANT SELECT ON database_stats TO istanbulplus_user;

-- Create a function to get database size
CREATE OR REPLACE FUNCTION get_database_size()
RETURNS text AS $$
BEGIN
    RETURN pg_size_pretty(pg_database_size(current_database()));
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission on size function
GRANT EXECUTE ON FUNCTION get_database_size() TO istanbulplus_user;

-- Set up logging
\echo 'Database initialization completed successfully!'
\echo 'Database: istanbulplus_db'
\echo 'User: istanbulplus_user'
\echo 'Timezone: Asia/Tehran'
\echo 'Extensions: uuid-ossp, pg_trgm, unaccent'
