#!/usr/bin/env bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-SQL
    CREATE DATABASE patients_test_db;
    GRANT ALL PRIVILEGES ON DATABASE patients_test_db TO $POSTGRES_USER;
SQL
