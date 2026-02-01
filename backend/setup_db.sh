#!/bin/bash
set -e

# Configuration
DB_NAME="fractal_workspace"
DB_USER="fractal"
DB_PASS="fractal123"
PG_HOST="localhost"
PG_PORT="5432"
SUPERUSER="postgres"

echo "Setting up PostgreSQL database..."

# Check if user exists, create if not
if ! psql -h "$PG_HOST" -p "$PG_PORT" -U "$SUPERUSER" -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
    echo "Creating user '$DB_USER'..."
    psql -h "$PG_HOST" -p "$PG_PORT" -U "$SUPERUSER" -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
else
    echo "User '$DB_USER' already exists."
fi

# Check if database exists, create if not
if ! psql -h "$PG_HOST" -p "$PG_PORT" -U "$SUPERUSER" -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1; then
    echo "Creating database '$DB_NAME'..."
    psql -h "$PG_HOST" -p "$PG_PORT" -U "$SUPERUSER" -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
else
    echo "Database '$DB_NAME' already exists."
fi

echo "Setup complete."
