# DataContractIQ Implementation Plan (Using IBM Bob)

## Overview

DataContractIQ is an AI-powered data contract generation and drift detection tool that uses IBM Bob to automatically analyze existing database schemas and pipeline code, extract implicit business rules, and generate formal human-readable data contracts.

**Demo Database:** Pagila (DVD rental database with 21 tables)

---

## Phase 1: Project Foundation & Database Setup

**Tasks:**
- Create project directory structure with backend and frontend folders
- Initialize Python FastAPI project with virtual environment
- Set up PostgreSQL database locally
- Load Pagila database schema from `GreenCycleBikes/pagila-master/pagila-insert-data.sql`
- Initialize React + TypeScript frontend with Vite
- Configure environment variables for database connection
- Install core dependencies: FastAPI, SQLAlchemy, psycopg2, React, TailwindCSS
- **Set up IBM Bob integration** (no API keys needed - Bob has direct workspace access)

**Complete When:**
- FastAPI server runs on `http://localhost:8000` with health check endpoint
- PostgreSQL contains Pagila database with all 21 tables
- React app runs on `http://localhost:5173` with basic landing page
- Can connect to database from Python and query table list
- Environment variables properly configured and loaded
- **IBM Bob can access the workspace and database files**

---

## Phase 2: Schema Introspection Engine

**Tasks:**
- Build SQL DDL parser to read `.sql` files
- Create data models for schema metadata (tables, columns, constraints, relationships)
- Implement SQLAlchemy introspection to extract schema from live database
- Parse table structures: columns, data types, nullability, defaults
- Extract constraints: primary keys, foreign keys, unique constraints, check constraints
- Identify relationships between tables via foreign key analysis
- Build API endpoint: `POST /api/schema/introspect` accepting SQL file or database connection
- Create schema snapshot storage mechanism (JSON format)
- **Prepare schema context files that Bob can read directly**

**Complete When:**
- Can parse `pagila-insert-data.sql` and extract all table definitions
- Successfully introspects live Pagila database via SQLAlchemy
- Returns structured JSON with complete metadata for all 21 tables
- Correctly identifies all foreign key relationships (e.g., `film.language_id` → `language.language_id`)
- Captures custom types (e.g., `mpaa_rating` enum) and domains (e.g., `year`)
- API endpoint returns schema metadata in <5 seconds for Pagila database
- **Schema metadata saved in workspace where Bob can access it**

---

## Phase 3: AI Contract Generation with IBM Bob (Stage 1)

**Tasks:**
- **Design Bob interaction workflow** - Bob reads schema files directly from workspace
- **Create prompt strategy** that leverages Bob's context awareness:
  - Bob reads entire `pagila-insert-data.sql` file
  - Bob analyzes all table relationships simultaneously
  - Bob understands full database context without token limits
- Build contract generator that asks Bob to:
  - Analyze table purpose from structure and relationships
  - Infer column meanings from names, types, and constraints
  - Extract business rules from defaults, checks, and patterns
  - Identify cross-table dependencies and data flows
  - Flag ambiguities that require human clarification
- Implement Bob response parser to extract structured contract data
- Generate targeted questions for human review (multiple-choice format)
- Convert Bob's analysis to JSON and Markdown formats
- Create API endpoint: `POST /api/contracts/generate` that invokes Bob
- **Leverage Bob's ability to read sample data** from database for better inference

**Complete When:**
- Bob successfully reads and analyzes `pagila-insert-data.sql` in full context
- Generates contract for `film` table with accurate descriptions
- Bob correctly infers business rules (e.g., `rental_duration` defaults to 3 days)
- Bob identifies relationships across entire schema (e.g., film → language, film → film_actor → actor)
- Bob flags 2-3 ambiguities with specific questions (e.g., "What values are in `special_features` array?")
- Generates contracts for `customer`, `rental`, and `payment` tables
- **Bob provides richer context** by analyzing actual data patterns in database
- Output includes both JSON (machine-readable) and Markdown (human-readable) formats
- Generation completes efficiently with Bob's full-context understanding

---

## Phase 4: Review Interface (Stage 2)

**Tasks:**
- Build React component: `ContractViewer` to display Bob-generated contracts
- Implement Markdown renderer with syntax highlighting
- Create `QuestionCard` component for ambiguity resolution
- Build multiple-choice question interface with Bob-suggested answers
- Implement inline editing capability for contract corrections
- Add approval workflow with digital signature/timestamp
- Create contract storage system (JSON files with metadata)
- Build version control: track contract changes with diffs
- Implement API endpoints:
  - `GET /api/contracts/:id` - Retrieve contract
  - `PUT /api/contracts/:id` - Update contract
  - `POST /api/contracts/:id/approve` - Approve contract
- Create contract list view showing all generated/approved contracts
- **Add "Ask Bob" button** for clarification on any contract section

**Complete When:**
- UI displays Bob-generated contract in clean, readable format
- Can view contract for `film` table with all sections
- Question cards show Bob-flagged ambiguities with 3-4 answer options
- User can select answers and add custom notes
- Inline editing works for correcting Bob-generated descriptions
- **"Ask Bob" feature allows users to request additional context**
- Approval button saves contract with timestamp and user signature
- Approved contracts stored in `data/contracts/` directory
- Can view contract history showing all versions and changes
- UI is responsive and works on desktop browsers

---

## Phase 5: Drift Detection System with Bob (Stage 3)

**Tasks:**
- Build schema comparison engine to detect differences
- Implement change detection for:
  - Added/removed tables
  - Added/removed columns
  - Data type modifications
  - Constraint changes (nullability, defaults, checks)
  - Relationship changes (foreign keys)
- **Use Bob to analyze drift impact** - Bob reads both old and new schemas
- **Bob provides intelligent impact analysis** by understanding:
  - Which downstream queries will break
  - Which business rules are violated
  - What data quality issues may arise
- Create drift classification system (breaking vs. non-breaking changes)
- Build alert generation logic with Bob-enhanced descriptions
- Implement alert storage and retrieval system
- Build monitoring dashboard showing:
  - Active contracts
  - Detected drifts
  - Alert history
  - Contract compliance status
- Implement API endpoints:
  - `POST /api/drift/detect` - Run drift detection with Bob analysis
  - `GET /api/drift/alerts` - Retrieve alerts
  - `PUT /api/drift/alerts/:id/acknowledge` - Acknowledge alert
- Add scheduled job capability for continuous monitoring

**Complete When:**
- Can compare current schema against approved contract
- Detects simulated change: adding column to `film` table
- **Bob analyzes impact** and generates detailed alert: "Added column: `digital_format VARCHAR(20)`"
- Alert includes Bob's assessment of contract violation and severity
- **Bob identifies affected downstream systems** by analyzing query patterns
- Dashboard displays active alerts with color-coded badges
- Can view detailed change comparison (before/after side-by-side)
- **Bob provides remediation suggestions** for detected drifts
- Alerts persist in database and can be retrieved via API
- Manual drift detection with Bob analysis completes in <15 seconds

---

## Phase 6: Demo Integration & Testing

**Tasks:**
- Create end-to-end demo scenario using Pagila database
- Build demo script showcasing Bob's capabilities:
  1. **Bob reads entire Pagila schema** and generates contract for `film` table
  2. Review interface shows Bob's analysis with sample questions
  3. Simulate schema change and **Bob detects drift with intelligent impact analysis**
- Add sample data visualizations (table relationships diagram)
- Create demo navigation flow between stages
- Implement error handling and user feedback messages
- Add loading states and progress indicators
- Write README with setup instructions
- Create demo presentation deck highlighting **Bob's context-aware advantages**
- Test complete workflow with 3+ tables
- Verify all API endpoints work correctly
- Test UI responsiveness and usability
- **Demonstrate Bob's superior understanding** vs. traditional AI approaches

**Complete When:**
- Can run complete demo from start to finish in <5 minutes
- Stage 1: **Bob generates comprehensive contract** for `film` table with full context
- Stage 2: Review interface shows Bob's questions, user approves contract
- Stage 3: **Bob detects drift and provides intelligent impact analysis**
- All UI components render correctly without errors
- API responses are fast (<2 seconds for most operations)
- Demo is reproducible on fresh installation
- README includes clear setup and run instructions
- Presentation deck explains **Bob's unique advantages**: full context awareness, no token limits, direct workspace access
- System handles edge cases gracefully (missing data, errors)
- Demo is ready for hackathon presentation

---

## IBM Bob Advantages for DataContractIQ

**Why Bob is Superior:**
- **Full Context Awareness**: Bob reads entire `pagila-insert-data.sql` without token limits
- **Workspace Integration**: Bob accesses database files, sample data, and existing documentation directly
- **Cross-Table Intelligence**: Bob understands relationships across all 21 tables simultaneously
- **No API Costs**: Bob is integrated into the development environment
- **Iterative Refinement**: Bob can be asked follow-up questions for clarification
- **Code Understanding**: Bob can analyze downstream pipeline code to assess drift impact

---

## Project Structure

```
datacontractiq/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── contracts.py      # Contract generation endpoints
│   │   │   ├── drift.py          # Drift detection endpoints
│   │   │   ├── schema.py         # Schema introspection endpoints
│   │   ├── core/
│   │   │   ├── schema_parser.py  # SQL parsing logic
│   │   │   ├── bob_engine.py     # IBM Bob integration
│   │   │   ├── drift_detector.py # Schema comparison
│   │   ├── models/
│   │   │   ├── schema.py         # Schema data models
│   │   │   ├── contract.py       # Contract data models
│   │   │   ├── alert.py          # Alert data models
│   │   ├── main.py               # FastAPI application
│   ├── requirements.txt
│   ├── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ContractViewer.tsx
│   │   │   ├── QuestionCard.tsx
│   │   │   ├── DriftAlert.tsx
│   │   │   ├── SchemaViewer.tsx
│   │   ├── pages/
│   │   │   ├── Generate.tsx
│   │   │   ├── Review.tsx
│   │   │   ├── Monitor.tsx
│   │   ├── App.tsx
│   ├── package.json
│   ├── vite.config.ts
├── data/
│   ├── pagila-insert-data.sql    # Sample database
│   ├── contracts/                # Approved contracts
│   ├── snapshots/                # Schema snapshots
├── docs/
│   ├── IMPLEMENTATION_PLAN.md    # This file
│   ├── API.md                    # API documentation
│   ├── DEMO_SCRIPT.md            # Demo walkthrough
├── README.md
└── .gitignore
```

---

## Success Criteria Summary

**Phase 1:** Development environment operational with Bob integration  
**Phase 2:** Schema metadata extracted and accessible to Bob  
**Phase 3:** Bob generates accurate contracts with full database context  
**Phase 4:** User reviews Bob-generated contracts with "Ask Bob" feature  
**Phase 5:** Bob detects drift and provides intelligent impact analysis  
**Phase 6:** Demo showcases Bob's context-aware advantages over traditional AI

---

## Technology Stack

**Backend:**
- Python 3.11+
- FastAPI
- SQLAlchemy
- psycopg2 (PostgreSQL driver)
- Pydantic (data validation)

**Frontend:**
- React 18+
- TypeScript
- Vite
- TailwindCSS
- React Query (state management)
- React Markdown (contract rendering)

**Database:**
- PostgreSQL 14+
- Pagila sample database

**AI:**
- IBM Bob (context-aware AI assistant)

**Development Tools:**
- Git
- VS Code
- Docker (optional for PostgreSQL)

---

## Next Steps

1. Review this implementation plan
2. Set up development environment (Phase 1)
3. Begin with schema introspection (Phase 2)
4. Iterate through phases, validating completion criteria at each step
5. Prepare demo presentation materials
6. Practice demo walkthrough

---

*This plan is designed for iterative development with clear completion criteria at each phase to ensure steady progress toward a working demo.*