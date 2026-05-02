# Skill: Schema Analysis

## Purpose
Analyze database schemas to extract metadata, relationships, constraints, and business rules for data contract generation.

## When to Use
- Analyzing SQL DDL files
- Introspecting live databases
- Extracting schema metadata for contract generation
- Understanding table relationships and dependencies

## Process

### 1. Initial Schema Discovery
- Read SQL file or connect to database
- List all tables, views, and materialized views
- Identify custom types (enums, domains)
- Document database version and features

### 2. Table-Level Analysis
For each table:
- Extract table name and purpose (infer from name)
- Identify primary key columns
- List all columns with data types
- Document table-level constraints
- Note indexes and their purposes

### 3. Column-Level Analysis
For each column:
- Data type (including precision/scale for numeric types)
- Nullability (NOT NULL constraint)
- Default values
- Check constraints
- Unique constraints
- Auto-increment/sequence usage
- Special types (arrays, JSON, custom types)

### 4. Relationship Mapping
- Identify all foreign key constraints
- Determine relationship cardinality (1:1, 1:N, N:M)
- Map relationship direction (parent → child)
- Identify junction tables for many-to-many relationships
- Document cascading rules (ON DELETE, ON UPDATE)

### 5. Business Rule Extraction
Look for implicit business rules:
- Default values indicating business logic
- Check constraints defining valid ranges
- Naming patterns suggesting purpose
- Timestamp columns for audit trails
- Status/state columns with enums
- Soft delete patterns (deleted_at, is_active)

### 6. Pattern Recognition
Identify common patterns:
- Audit columns (created_at, updated_at, created_by)
- Versioning patterns (version, revision_number)
- Hierarchical structures (parent_id, path)
- Polymorphic associations (type + id columns)
- Temporal data (valid_from, valid_to)

## Output Format

```json
{
  "table_name": "film",
  "purpose": "Stores DVD film catalog information",
  "columns": [
    {
      "name": "film_id",
      "type": "integer",
      "nullable": false,
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "title",
      "type": "text",
      "nullable": false,
      "description": "Film title"
    },
    {
      "name": "rental_duration",
      "type": "smallint",
      "nullable": false,
      "default": "3",
      "business_rule": "Default rental period is 3 days"
    }
  ],
  "relationships": [
    {
      "type": "foreign_key",
      "column": "language_id",
      "references": "language.language_id",
      "cardinality": "N:1"
    }
  ],
  "constraints": [
    {
      "type": "check",
      "expression": "rental_duration > 0",
      "business_rule": "Rental duration must be positive"
    }
  ]
}
```

## Tools to Use
- `read_file` - Read SQL DDL files
- `search_files` - Find specific patterns (CREATE TABLE, FOREIGN KEY)
- `list_code_definition_names` - Get overview of database objects

## Common Patterns

### PostgreSQL-Specific
- Custom ENUM types
- DOMAIN types with constraints
- Array columns
- JSONB columns
- Full-text search (tsvector)
- Sequences for auto-increment

### Naming Conventions
- `_id` suffix → Primary/Foreign key
- `_at` suffix → Timestamp
- `_by` suffix → User reference
- `is_` prefix → Boolean flag
- `has_` prefix → Boolean flag

## Validation Checklist
- [ ] All tables identified
- [ ] All columns documented with types
- [ ] All foreign keys mapped
- [ ] Primary keys identified
- [ ] Constraints extracted
- [ ] Business rules inferred
- [ ] Relationships validated
- [ ] Custom types documented

## Example Usage

```python
# Introspect Pagila database
schema = analyze_schema("pagila-insert-data.sql")

# Extract film table metadata
film_table = schema.get_table("film")

# Get all relationships
relationships = film_table.get_relationships()

# Infer business rules
rules = extract_business_rules(film_table)