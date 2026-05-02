# Implementation Rules

## Strict Development Rules
1. **ONE FILE AT A TIME** - Never create multiple files in a single step
2. **EXPLAIN EACH FILE** - After creating, explain what it does and how it fits
3. **VERIFY IMPORTS** - Ensure all imports exist before writing code
4. **MATCH PROJECT STRUCTURE** - Follow existing patterns in backend/app
5. **ASK BEFORE PROCEEDING** - If uncertain about DB, schema, or config, STOP and ASK
6. **WAIT FOR CONFIRMATION** - After each file, wait for user approval before next file


## Existing Project Context
- **Models**: `backend/app/models/schema.py` already has complete Pydantic models
- **Config**: `backend/app/config.py` has database_url, file paths configured
- **Dependencies**: SQLAlchemy 2.0.25, psycopg2-binary, pydantic, FastAPI all installed
- **Database**: PostgreSQL with Pagila database (21 tables)
- **SQL File**: `GreenCycleBikes/pagila-master/pagila-insert-data.sql`

## Before Writing Any Code
- Check if required dependencies exist
- Verify file paths are correct
- Confirm database connection details
- Review existing code patterns

## Bob's Reminder to Self
STOP and ASK if:
- Database connection string unclear
- SQL file format unexpected
- Missing dependencies discovered
- Uncertain about schema structure
- Need clarification on requirements