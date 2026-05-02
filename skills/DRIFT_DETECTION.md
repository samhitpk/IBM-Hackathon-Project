# Skill: Schema Drift Detection

## Purpose
Detect and analyze changes between approved data contracts and current database schemas, providing intelligent impact analysis.

## When to Use
- Monitoring schema changes in production
- Validating schema migrations
- Detecting unauthorized schema modifications
- Assessing impact of proposed changes

## Process

### 1. Capture Current State
- Introspect current database schema
- Extract complete metadata (use SCHEMA_ANALYSIS skill)
- Create schema snapshot with timestamp
- Store snapshot for historical comparison

### 2. Load Approved Contract
- Retrieve approved contract from storage
- Parse contract specifications
- Extract expected schema definition
- Note contract version and approval date

### 3. Compare Schemas

**Table-Level Changes:**
- Added tables (new tables not in contract)
- Removed tables (contract tables missing from schema)
- Renamed tables (detect via similarity analysis)

**Column-Level Changes:**
- Added columns
- Removed columns
- Renamed columns
- Data type changes
- Nullability changes
- Default value changes

**Constraint Changes:**
- Added/removed primary keys
- Added/removed foreign keys
- Added/removed unique constraints
- Added/removed check constraints
- Modified constraint definitions

**Relationship Changes:**
- New foreign key relationships
- Removed relationships
- Changed cardinality
- Modified cascade rules

### 4. Classify Changes

**Breaking Changes (High Severity):**
- Removed columns
- Removed tables
- Changed data types (incompatible)
- Added NOT NULL to existing column
- Removed foreign key constraints

**Non-Breaking Changes (Medium Severity):**
- Added nullable columns
- Added tables
- Added indexes
- Relaxed constraints (removed NOT NULL)

**Informational Changes (Low Severity):**
- Added comments
- Renamed with backward compatibility
- Performance optimizations

### 5. Use Bob for Impact Analysis

Leverage Bob's context awareness:

```
Bob, analyze this schema change:
- Table: film
- Change: Added column 'digital_format VARCHAR(20)'
- Approved contract: [contract details]

Please assess:
1. Does this violate the approved contract?
2. What downstream systems might be affected?
3. What queries might break?
4. What business rules are impacted?
5. What remediation steps are needed?
```

Bob can:
- Read downstream pipeline code
- Analyze query patterns
- Identify affected ETL jobs
- Suggest migration strategies

### 6. Generate Alerts

**Alert Structure:**
```json
{
  "alert_id": "drift_001",
  "severity": "high",
  "detected_at": "2026-05-01T19:00:00Z",
  "table": "film",
  "change_type": "column_added",
  "details": {
    "column_name": "digital_format",
    "data_type": "VARCHAR(20)",
    "nullable": true
  },
  "contract_violation": {
    "violated": true,
    "reason": "Unapproved schema modification",
    "contract_version": "1.0"
  },
  "impact_analysis": {
    "affected_queries": 3,
    "affected_pipelines": ["etl_film_sync", "analytics_film_report"],
    "breaking_change": false,
    "risk_level": "medium"
  },
  "recommendations": [
    "Update data contract to include new column",
    "Modify downstream queries to handle new field",
    "Add validation rules for digital_format values"
  ]
}
```

### 7. Create Comparison Report

**Side-by-Side Comparison:**
```markdown
## Schema Drift Report: film

### Changes Detected

#### Added Columns
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| digital_format | VARCHAR(20) | Yes | NULL |

**Contract Status:** ❌ Not in approved contract
**Impact:** Medium - 3 queries may need updates
**Recommendation:** Update contract and modify affected queries

### Affected Systems
- `etl_film_sync` - May need to handle new column
- `analytics_film_report` - Report schema may be incomplete
- `api_film_endpoint` - API response may be inconsistent
```

## Detection Strategies

### Scheduled Monitoring
```python
# Run every hour
def monitor_drift():
    current_schema = introspect_database()
    approved_contract = load_contract("film")
    
    changes = compare_schemas(current_schema, approved_contract)
    
    if changes:
        alert = generate_alert(changes)
        notify_stakeholders(alert)
```

### Event-Driven Detection
```python
# Trigger on schema change events
def on_schema_change(event):
    if event.type == "ALTER_TABLE":
        check_drift(event.table_name)
```

### Manual Validation
```python
# Before deployment
def validate_migration(migration_script):
    proposed_schema = parse_migration(migration_script)
    current_contract = load_contract()
    
    violations = check_contract_compliance(proposed_schema, current_contract)
    
    if violations:
        raise ContractViolationError(violations)
```

## Change Detection Algorithms

### Column Matching
```python
def match_columns(old_cols, new_cols):
    # Exact name match
    exact_matches = {c for c in old_cols if c in new_cols}
    
    # Fuzzy match for renames (Levenshtein distance)
    potential_renames = []
    for old_col in old_cols - exact_matches:
        for new_col in new_cols - exact_matches:
            if similarity(old_col, new_col) > 0.8:
                potential_renames.append((old_col, new_col))
    
    return exact_matches, potential_renames
```

### Type Compatibility
```python
def is_compatible_type_change(old_type, new_type):
    compatible_changes = {
        ("VARCHAR(50)", "VARCHAR(100)"): True,  # Widening
        ("INT", "BIGINT"): True,                # Widening
        ("VARCHAR(100)", "VARCHAR(50)"): False, # Narrowing
        ("INT", "VARCHAR"): False,              # Incompatible
    }
    return compatible_changes.get((old_type, new_type), False)
```

## Bob Integration for Impact Analysis

**Query Analysis:**
```
Bob, find all SQL queries in the codebase that reference the 'film' table
and determine which ones would be affected by removing the 'rental_duration' column.
```

**Pipeline Analysis:**
```
Bob, analyze the ETL pipeline code and identify which jobs read from or write to
the 'film' table. What would break if we change 'rating' from ENUM to VARCHAR?
```

**Business Rule Analysis:**
```
Bob, based on the approved contract, what business rules would be violated
if we allow NULL values in the 'rental_rate' column?
```

## Alert Prioritization

**Priority 1 (Critical):**
- Breaking changes in production
- Data loss risk
- Contract violations affecting SLAs

**Priority 2 (High):**
- Non-breaking contract violations
- Changes affecting multiple systems
- Missing required constraints

**Priority 3 (Medium):**
- Informational changes
- Performance impacts
- Documentation updates needed

**Priority 4 (Low):**
- Cosmetic changes
- Optimization opportunities
- Best practice suggestions

## Validation Checklist
- [ ] Current schema captured accurately
- [ ] Approved contract loaded correctly
- [ ] All change types detected
- [ ] Changes classified by severity
- [ ] Impact analysis completed
- [ ] Affected systems identified
- [ ] Alerts generated with details
- [ ] Recommendations provided
- [ ] Stakeholders notified

## Example Usage

```python
# Detect drift for film table
drift_report = detect_drift(
    table_name="film",
    current_schema=current_schema,
    approved_contract=contract,
    use_bob_analysis=True
)

# Check for violations
if drift_report.has_violations():
    alert = create_alert(drift_report)
    send_notification(alert)
    
# Generate comparison report
report = generate_comparison_report(drift_report)
save_report(report, "reports/drift_film_2026-05-01.md")
```

## Integration with Other Skills
- Uses output from **SCHEMA_ANALYSIS** skill
- Compares against **CONTRACT_GENERATION** output
- Triggers **CONTRACT_REVIEW** for updates
- Feeds into monitoring dashboards