# Skill: Data Contract Generation

## Purpose
Generate formal, human-readable data contracts from database schemas using IBM Bob's context-aware analysis.

## When to Use
- Creating initial data contracts from existing schemas
- Documenting implicit business rules
- Generating contracts for multiple related tables
- Producing both machine-readable and human-readable formats

## Process

### 1. Prepare Context for Bob
- Gather complete schema metadata (from SCHEMA_ANALYSIS skill)
- Include sample data if available
- Collect existing documentation
- Identify related tables and dependencies

### 2. Design Bob Prompt
Structure the prompt to leverage Bob's full-context awareness:

```
You are analyzing a database schema to generate a formal data contract.

Context:
- Database: [database_name]
- Table: [table_name]
- Full schema available in workspace
- Related tables: [list]

Task:
1. Analyze the table structure and infer its business purpose
2. Describe what each column represents in business terms
3. Extract business rules from constraints and defaults
4. Identify relationships and data flows
5. Flag any ambiguities that need human clarification

Output a structured contract with:
- Table purpose and context
- Column descriptions with semantic meaning
- Data quality rules
- Relationships to other tables
- Questions for human review (if any)
```

### 3. Parse Bob's Response
Extract structured information:
- Table purpose statement
- Column descriptions
- Business rules
- Relationship mappings
- Flagged ambiguities
- Suggested questions

### 4. Generate Contract Sections

**Section 1: Overview**
- Table name and purpose
- Business context
- Data owner/steward
- Update frequency

**Section 2: Schema Definition**
- Column specifications
- Data types with precision
- Nullability rules
- Default values

**Section 3: Business Rules**
- Validation rules
- Constraints
- Calculated fields
- Derived values

**Section 4: Relationships**
- Foreign key mappings
- Parent/child relationships
- Dependency graph

**Section 5: Quality Standards**
- Completeness requirements
- Accuracy expectations
- Timeliness SLAs
- Consistency rules

**Section 6: Questions for Review**
- Ambiguous column purposes
- Unclear business rules
- Missing constraints
- Validation needs

### 5. Format Output

**JSON Format (Machine-Readable):**
```json
{
  "contract_version": "1.0",
  "table": "film",
  "purpose": "Stores DVD film catalog information",
  "owner": "TBD",
  "columns": [...],
  "business_rules": [...],
  "relationships": [...],
  "quality_standards": {...},
  "questions": [...]
}
```

**Markdown Format (Human-Readable):**
```markdown
# Data Contract: film

## Overview
**Purpose:** Stores DVD film catalog information
**Owner:** [To be determined]
**Last Updated:** 2026-05-01

## Schema Definition
| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| film_id | integer | No | auto | Unique film identifier |
| title | text | No | - | Film title |
...

## Business Rules
1. Rental duration defaults to 3 days
2. Rating must be valid MPAA rating (G, PG, PG-13, R, NC-17)
...
```

## Ambiguity Detection

Flag these situations for human review:
- Generic column names (data, value, info)
- Arrays without clear content definition
- Nullable columns without clear business reason
- Missing constraints that should exist
- Unusual data type choices
- Relationships without clear cardinality

## Question Generation

Create targeted, multiple-choice questions:

**Bad (Open-ended):**
"What does the special_features column contain?"

**Good (Targeted):**
"What types of values are stored in the special_features array?"
- [ ] Bonus features (deleted scenes, commentary, etc.)
- [ ] Technical specifications (resolution, audio format)
- [ ] Marketing categories (family-friendly, action-packed)
- [ ] Other: [specify]

## Output Validation

Ensure contract includes:
- [ ] Clear table purpose statement
- [ ] All columns documented
- [ ] Data types specified with precision
- [ ] Business rules extracted from constraints
- [ ] Relationships mapped
- [ ] Quality standards defined
- [ ] Ambiguities flagged with questions
- [ ] Both JSON and Markdown formats generated

## Bob Integration Tips

**Leverage Bob's Strengths:**
- Let Bob read entire schema file at once
- Ask Bob to analyze cross-table relationships
- Request Bob to identify patterns across multiple tables
- Use Bob to suggest business meanings from naming conventions

**Example Bob Interaction:**
```
User: "Analyze the film table in pagila-insert-data.sql and generate a data contract"

Bob: [Reads entire file, analyzes relationships, generates contract]

User: "What business rule does the rental_duration default suggest?"

Bob: "The default value of 3 suggests a standard rental period of 3 days..."
```

## Common Patterns

### Audit Columns
```
created_at, updated_at → Track record lifecycle
created_by, updated_by → Track user actions
```

### Status Management
```
is_active, is_deleted → Soft delete pattern
status ENUM → Workflow states
```

### Versioning
```
version, revision → Track changes
valid_from, valid_to → Temporal validity
```

## Example Usage

```python
# Generate contract for film table
contract = generate_contract(
    table_name="film",
    schema_metadata=schema,
    use_bob=True
)

# Save in both formats
save_contract_json(contract, "contracts/film.json")
save_contract_markdown(contract, "contracts/film.md")

# Get questions for review
questions = contract.get_questions()
```

## Integration with Other Skills
- Uses output from **SCHEMA_ANALYSIS** skill
- Feeds into **CONTRACT_REVIEW** skill
- Provides baseline for **DRIFT_DETECTION** skill