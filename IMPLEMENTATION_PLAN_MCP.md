# DataContractIQ MCP Server Implementation Plan

## Overview

DataContractIQ is an **MCP (Model Context Protocol) server** that extends IBM Bob with data contract generation capabilities. The MCP server connects to databases or SQL files and exposes tools that Bob can call to automatically generate, manage, and monitor data contracts through natural conversation.

**Key Innovation:** Data engineers can open Bob in their IDE, connect to this MCP server, and through natural conversation with Bob, automatically generate formal data contracts for their entire database without writing any documentation manually.

---

## Architecture

### MCP Server Approach

```
┌─────────────────────────────────────────────────────────────┐
│                        IBM Bob (IDE)                         │
│                  (Natural Language Interface)                │
└────────────────────────┬────────────────────────────────────┘
                         │ MCP Protocol
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              DataContractIQ MCP Server                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  MCP Tools (7 tools exposed to Bob)                  │  │
│  │  • introspect_schema    • save_contract              │  │
│  │  • analyze_table        • list_contracts             │  │
│  │  • generate_contract    • detect_drift               │  │
│  │  • compare_schemas                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Core Modules (Reuse Phase 2 Code)                   │  │
│  │  • sql_parser.py        • contract_storage.py        │  │
│  │  • schema_introspector  • contract_formatter.py      │  │
│  │  • snapshot_manager     • contract models            │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         ↓
              ┌──────────────────────┐
              │  PostgreSQL Database  │
              │  (Pagila - 21 tables) │
              └──────────────────────┘
```

### What We Keep from Phase 2 ✅

All Phase 2 code remains **unchanged** and is wrapped by MCP tools:
- ✅ `backend/app/core/sql_parser.py` - Parse SQL DDL files
- ✅ `backend/app/core/schema_introspector.py` - Live DB introspection
- ✅ `backend/app/core/snapshot_manager.py` - Schema snapshots
- ✅ `backend/app/models/schema.py` - Schema data models
- ✅ `backend/app/db/database.py` - Database connections

### What We Add for Phase 3 🆕

New components for MCP server and contract management:
- 🆕 `backend/mcp_server.py` - Main MCP server with 7 tools
- 🆕 `backend/app/models/contract.py` - Contract data models
- 🆕 `backend/app/core/contract_storage.py` - Contract persistence
- 🆕 `backend/app/core/contract_formatter.py` - JSON ↔ Markdown
- 🆕 `backend/app/core/drift_detector.py` - Schema comparison
- 🆕 MCP SDK dependency in requirements.txt

---

## Phase 3: MCP Server Implementation

### Tasks

1. **Create Contract Data Models**
   - Define Pydantic models for contracts
   - Include: table info, columns, business rules, relationships
   - Support for questions/ambiguities flagged by Bob
   - Metadata: version, author, approval status, timestamps

2. **Build Contract Storage System**
   - Save contracts as JSON in `data/contracts/`
   - Load and list existing contracts
   - Version control for contract updates
   - Search/filter contracts by table or status

3. **Implement Contract Formatter**
   - Convert JSON contracts to Markdown for display
   - Generate human-readable documentation
   - Include table of contents, sections, examples
   - Support for exporting to different formats

4. **Create Drift Detection Engine**
   - Compare current schema vs. approved contract
   - Identify breaking vs. non-breaking changes
   - Generate detailed change reports
   - Classify severity (critical, warning, info)

5. **Build MCP Server with 7 Tools**
   - Implement MCP protocol using Python SDK
   - Expose 7 tools for Bob to call
   - Handle tool parameters and responses
   - Error handling and validation

6. **Update Dependencies**
   - Add MCP SDK to requirements.txt
   - Verify compatibility with existing packages
   - Document installation steps

### MCP Tools Specification

#### 1. `introspect_schema`
**Purpose:** Read and analyze database schema from SQL file or live database

**Parameters:**
- `source_type`: "file" or "database"
- `source_path`: Path to SQL file (optional)
- `tables`: List of specific tables (optional, default: all)

**Returns:**
- Complete schema metadata (JSON)
- Table count, relationships, custom types
- Introspection time

**Example Bob Usage:**
```
Bob: "Introspect the Pagila database"
Tool Call: introspect_schema(source_type="database")
```

#### 2. `analyze_table`
**Purpose:** Deep analysis of a specific table's structure and relationships

**Parameters:**
- `table_name`: Name of table to analyze
- `include_sample_data`: Boolean (default: false)
- `max_samples`: Number of sample rows (default: 10)

**Returns:**
- Table structure (columns, types, constraints)
- Foreign key relationships (incoming/outgoing)
- Business rules inferred from constraints
- Sample data (if requested)
- Suggested contract sections

**Example Bob Usage:**
```
Bob: "Analyze the film table in detail"
Tool Call: analyze_table(table_name="film", include_sample_data=true)
```

#### 3. `generate_contract`
**Purpose:** Generate a plain English data contract for a table

**Parameters:**
- `table_name`: Table to generate contract for
- `schema_metadata`: Schema info from introspect_schema
- `include_examples`: Boolean (default: true)
- `format`: "json" or "markdown" (default: "both")

**Returns:**
- Contract in JSON format
- Contract in Markdown format (if requested)
- List of ambiguities/questions for human review
- Confidence score for each section

**Example Bob Usage:**
```
Bob: "Generate a data contract for the customer table"
Tool Call: generate_contract(table_name="customer", format="both")
```

**Contract Structure:**
```json
{
  "table_name": "customer",
  "description": "Stores customer information for the DVD rental business",
  "columns": [
    {
      "name": "customer_id",
      "description": "Unique identifier for each customer",
      "data_type": "integer",
      "constraints": ["PRIMARY KEY", "AUTO INCREMENT"],
      "business_rules": ["Must be unique", "System-generated"]
    }
  ],
  "relationships": [
    {
      "type": "foreign_key",
      "column": "address_id",
      "references": "address.address_id",
      "description": "Links customer to their address"
    }
  ],
  "business_rules": [
    "Customers must have a valid email address",
    "Active customers have active=1"
  ],
  "questions": [
    {
      "question": "What is the retention policy for inactive customers?",
      "context": "No explicit constraint found",
      "suggested_answers": [
        "Keep indefinitely",
        "Archive after 2 years",
        "Delete after 5 years"
      ]
    }
  ]
}
```

#### 4. `save_contract`
**Purpose:** Save an approved data contract

**Parameters:**
- `contract`: Contract object (JSON)
- `approved_by`: User who approved (optional)
- `notes`: Approval notes (optional)

**Returns:**
- Contract ID
- File path where saved
- Timestamp

**Example Bob Usage:**
```
Bob: "Save this contract as approved"
Tool Call: save_contract(contract={...}, approved_by="user@example.com")
```

#### 5. `list_contracts`
**Purpose:** List all existing data contracts

**Parameters:**
- `status`: Filter by status (optional: "draft", "approved", "outdated")
- `table_name`: Filter by table (optional)

**Returns:**
- List of contracts with metadata
- Count by status
- Last updated timestamps

**Example Bob Usage:**
```
Bob: "Show me all approved contracts"
Tool Call: list_contracts(status="approved")
```

#### 6. `detect_drift`
**Purpose:** Compare current schema against approved contract

**Parameters:**
- `table_name`: Table to check
- `contract_id`: Contract to compare against (optional: uses latest)

**Returns:**
- List of detected changes
- Severity classification (critical, warning, info)
- Impact assessment
- Recommendations

**Example Bob Usage:**
```
Bob: "Check if the film table has drifted from its contract"
Tool Call: detect_drift(table_name="film")
```

**Drift Report Structure:**
```json
{
  "table_name": "film",
  "contract_version": "v1.0",
  "drift_detected": true,
  "changes": [
    {
      "type": "column_added",
      "column": "digital_format",
      "severity": "warning",
      "description": "New column 'digital_format' added",
      "impact": "Contract needs update, queries may need modification",
      "recommendation": "Update contract to include new column"
    }
  ],
  "summary": {
    "critical": 0,
    "warnings": 1,
    "info": 0
  }
}
```

#### 7. `compare_schemas`
**Purpose:** Compare two schema snapshots to see what changed

**Parameters:**
- `snapshot_id_1`: First snapshot ID
- `snapshot_id_2`: Second snapshot ID (optional: uses current)
- `table_name`: Specific table (optional: all tables)

**Returns:**
- Detailed comparison report
- Added/removed/modified tables
- Column changes
- Constraint changes

**Example Bob Usage:**
```
Bob: "Compare the current schema with yesterday's snapshot"
Tool Call: compare_schemas(snapshot_id_1="pagila_20260501_120000")
```

---

## Conversation Flow Examples

### Example 1: Initial Contract Generation

```
User: "Bob, I need to document my Pagila database"

Bob: "I'll help you create data contracts. Let me start by introspecting your database."
[Calls: introspect_schema(source_type="database")]

Bob: "I found 21 tables in your Pagila database. Which tables would you like to document first?"

User: "Start with the film table"

Bob: "Let me analyze the film table in detail."
[Calls: analyze_table(table_name="film", include_sample_data=true)]

Bob: "The film table stores movie information with 14 columns. I'll generate a data contract."
[Calls: generate_contract(table_name="film")]

Bob: "I've generated a contract for the film table. Here are a few questions:
1. What values are allowed in the special_features array?
2. What's the business rule for rental_duration defaults?

Would you like to review and approve this contract?"

User: "Yes, looks good. Save it."

Bob: "Contract saved!"
[Calls: save_contract(contract={...}, approved_by="user")]
```

### Example 2: Drift Detection

```
User: "Bob, check if my database schema has changed"

Bob: "I'll compare the current schema against your approved contracts."
[Calls: detect_drift(table_name="film")]

Bob: "⚠️ Drift detected in the film table:
- New column added: 'digital_format VARCHAR(20)'
- Severity: Warning
- Impact: Contract needs update

Would you like me to update the contract?"

User: "Yes, update it"

Bob: "I'll regenerate the contract with the new column."
[Calls: generate_contract(table_name="film")]
[Calls: save_contract(contract={...})]

Bob: "Contract updated and saved!"
```

---

## Implementation Steps

### Step 1: Create Contract Models
**File:** `backend/app/models/contract.py`

Define Pydantic models for:
- `DataContract` - Main contract structure
- `ColumnContract` - Column-level documentation
- `BusinessRule` - Business rule definition
- `ContractQuestion` - Ambiguity flagged for review
- `ContractMetadata` - Version, approval, timestamps

### Step 2: Build Contract Storage
**File:** `backend/app/core/contract_storage.py`

Implement:
- `save_contract()` - Save to `data/contracts/`
- `load_contract()` - Load by ID or table name
- `list_contracts()` - List with filters
- `delete_contract()` - Remove contract
- `get_latest_contract()` - Get most recent version

### Step 3: Create Contract Formatter
**File:** `backend/app/core/contract_formatter.py`

Implement:
- `contract_to_markdown()` - Convert JSON to Markdown
- `markdown_to_contract()` - Parse Markdown back to JSON
- `generate_toc()` - Table of contents
- `format_business_rules()` - Format rules section
- `format_relationships()` - Format relationships diagram

### Step 4: Build Drift Detector
**File:** `backend/app/core/drift_detector.py`

Implement:
- `detect_drift()` - Compare schema vs contract
- `classify_change()` - Determine severity
- `generate_drift_report()` - Create detailed report
- `suggest_remediation()` - Recommend fixes

### Step 5: Implement MCP Server
**File:** `backend/mcp_server.py`

Implement:
- MCP server initialization
- 7 tool definitions with schemas
- Tool handlers calling Phase 2 code
- Error handling and logging
- Server startup and shutdown

### Step 6: Update Dependencies
**File:** `backend/requirements.txt`

Add:
```
mcp>=0.1.0  # MCP SDK
```

---

## Success Criteria

### Phase 3 Complete When:

✅ **MCP Server Running**
- Server starts without errors
- Connects to Bob successfully
- All 7 tools registered and callable

✅ **Contract Generation Working**
- Bob can introspect Pagila database
- Generates accurate contracts for film, customer, rental tables
- Contracts include descriptions, business rules, relationships
- Questions flagged for ambiguous cases

✅ **Contract Storage Working**
- Contracts saved to `data/contracts/`
- Can list and retrieve contracts
- Version control tracks changes

✅ **Drift Detection Working**
- Detects schema changes accurately
- Classifies severity correctly
- Generates actionable reports

✅ **Natural Conversation Flow**
- User can ask Bob to document database
- Bob guides user through process
- Minimal manual intervention needed

---

## Technology Stack

**MCP Server:**
- Python 3.11+
- MCP SDK (official Python implementation)
- FastAPI (for optional REST API)

**Reused from Phase 2:**
- SQLAlchemy (database introspection)
- Pydantic (data validation)
- psycopg2 (PostgreSQL driver)

**New Dependencies:**
- MCP SDK
- Markdown library (for formatting)

**Frontend (Optional):**
- React + TypeScript (for visualization)
- Markdown renderer
- Diff viewer for drift reports

---

## Project Structure (Updated)

```
datacontractiq/
├── backend/
│   ├── mcp_server.py              # 🆕 Main MCP server
│   ├── app/
│   │   ├── models/
│   │   │   ├── schema.py          # ✅ Phase 2 (unchanged)
│   │   │   ├── contract.py        # 🆕 Contract models
│   │   ├── core/
│   │   │   ├── sql_parser.py      # ✅ Phase 2 (unchanged)
│   │   │   ├── schema_introspector.py  # ✅ Phase 2 (unchanged)
│   │   │   ├── snapshot_manager.py     # ✅ Phase 2 (unchanged)
│   │   │   ├── contract_storage.py     # 🆕 Contract persistence
│   │   │   ├── contract_formatter.py   # 🆕 JSON ↔ Markdown
│   │   │   ├── drift_detector.py       # 🆕 Schema comparison
│   │   ├── db/
│   │   │   ├── database.py        # ✅ Phase 2 (unchanged)
│   ├── requirements.txt           # 🆕 Add MCP SDK
├── data/
│   ├── contracts/                 # 🆕 Approved contracts
│   ├── snapshots/                 # ✅ Schema snapshots
├── docs/
│   ├── IMPLEMENTATION_PLAN_MCP.md # 🆕 This file
│   ├── MCP_TOOLS.md              # 🆕 Tool documentation
├── README.md
```

---

## Next Steps

1. ✅ Review and approve this implementation plan
2. Create contract data models (`contract.py`)
3. Build contract storage system (`contract_storage.py`)
4. Implement contract formatter (`contract_formatter.py`)
5. Create drift detector (`drift_detector.py`)
6. Build MCP server with 7 tools (`mcp_server.py`)
7. Update dependencies (add MCP SDK)
8. Test with Bob in IDE
9. Create demo video showing natural conversation flow
10. Document setup and usage

---

## Demo Scenario

**Goal:** Show how a data engineer can document their entire database through conversation with Bob

**Steps:**
1. User opens Bob in VS Code
2. Bob connects to DataContractIQ MCP server
3. User: "Bob, help me document my Pagila database"
4. Bob introspects database, suggests starting with key tables
5. Bob generates contracts for film, customer, rental tables
6. User reviews and approves contracts
7. User makes schema change (adds column)
8. Bob detects drift and alerts user
9. Bob updates contract with new column
10. Complete documentation generated in <5 minutes

**Key Differentiator:** No manual documentation writing, no context switching, natural conversation flow

---

*This plan leverages the MCP architecture to create a seamless experience where Bob becomes a data documentation assistant, making contract generation effortless.*