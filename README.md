# DataContractIQ

**AI-Powered Data Contract Management with Real-Time Drift Detection**

Automatically generate, review, and monitor data contracts for your PostgreSQL databases. Get instant alerts when schema changes violate approved contracts.

---

## 🎯 Overview

DataContractIQ is an intelligent data governance tool that:
1. **Generates** comprehensive data contracts from existing database schemas using AI
2. **Facilitates** human review and approval with targeted questions
3. **Monitors** for schema drift in real-time with event-driven alerts

Built for the IBM Hackathon 2026, leveraging IBM Bob's MCP (Model Context Protocol) for context-aware schema analysis.

---

## ✨ Key Features

### 🤖 AI-Powered Contract Generation
- Automatic schema introspection and analysis
- Intelligent business rule extraction
- Relationship mapping across tables
- Example value generation
- Ambiguity detection with targeted questions

### 👥 Interactive Review & Approval
- User-friendly web interface
- Question-driven clarification workflow
- Answer suggestions based on schema patterns
- Approval tracking with timestamps
- Contract versioning

### 🚨 Real-Time Drift Detection
- **30-second polling** for schema changes
- **Event-driven alerts** when violations occur
- **Severity classification** (Critical/Warning/Info)
- **Visual indicators** (green ✓ OK / red ✗ Drift badges)
- **Detailed change reports** with impact analysis
- **Breaking change detection**

### 🎨 Modern UI/UX
- Clean, responsive React interface
- TailwindCSS styling
- Real-time status updates
- Prominent alert banners
- Contract cards with drift indicators

---

## 🏗️ Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   React UI      │◄────►│  FastAPI Backend │◄────►│   PostgreSQL    │
│  (Frontend)     │      │   + MCP Server   │      │    Database     │
└─────────────────┘      └──────────────────┘      └─────────────────┘
        │                         │
        │                         │
        ▼                         ▼
  Polling Service          Drift Detection
  (30s interval)           Service Layer
        │                         │
        └─────────┬───────────────┘
                  │
                  ▼
            Alert System
```

**Components:**
- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS
- **Backend**: FastAPI + SQLAlchemy + Pydantic
- **AI Engine**: IBM Bob MCP Server for schema analysis
- **Database**: PostgreSQL 14+ (Pagila demo database)
- **Monitoring**: Polling-based drift detection (30-second intervals)

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **PostgreSQL** 14+

### Installation

**1. Clone and Setup Database**
```bash
# Create database
psql -U your_username
CREATE DATABASE pagila;
\q

# Load sample data
psql -U your_username -d pagila -f GreenCycleBikes/pagila-master/pagila-insert-data.sql
```

**2. Backend Setup**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure database (update backend/app/config.py)
# database_url: str = "postgresql://your_username@localhost:5432/pagila"

# Start backend server
python -m uvicorn app.main:app --reload
```

**3. Frontend Setup**
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Access Points

- **Frontend UI**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MCP Server**: Integrated with backend

---

## 🎬 Quick Demo

### Generate and Approve a Contract

1. Open frontend at http://localhost:5173
2. Use MCP tools to generate a contract:
   ```
   Ask Bob: "Generate a data contract for the rental table"
   ```
3. Review the contract in the UI
4. Answer questions (optional)
5. Enter your name and click "Approve Contract"

### Test Drift Detection

1. **Verify clean state** - Contract shows green "OK" badge
2. **Break the contract** - Open PostgreSQL terminal:
   ```sql
   ALTER TABLE rental DROP COLUMN return_date;
   ```
3. **Watch alert appear** - Within 30 seconds, red banner shows:
   ```
   ⚠️ Schema Drift Detected
   rental: 1 change(s)
   🔴 1 CRITICAL change(s) detected
   ```
4. **Fix the issue**:
   ```sql
   ALTER TABLE rental ADD COLUMN return_date TIMESTAMP;
   ```
5. **Alert clears** - Within 30 seconds, green "OK" badge returns

---

## 📚 How It Works

### Stage 1: Contract Generation
1. MCP server introspects database schema
2. AI analyzes tables, columns, relationships, constraints
3. Generates comprehensive contract with:
   - Column descriptions and data types
   - Business rules and constraints
   - Relationship mappings
   - Data quality rules
   - Questions for human review

### Stage 2: Human Review
1. Contract displayed in web interface
2. Reviewer answers clarification questions
3. Suggested answers provided based on patterns
4. Reviewer approves contract with their name
5. Contract saved as "approved" with timestamp

### Stage 3: Drift Detection
1. **Polling service** checks every 30 seconds
2. **Drift detector** compares current schema vs approved contract
3. **Changes classified** by severity:
   - 🔴 **Critical**: Column removed, type changed, NOT NULL added
   - 🟡 **Warning**: Column added, nullable changed
   - 🔵 **Info**: Comment updated, default changed
4. **Alert banner** displays when drift detected
5. **Visual badges** show status on contract cards

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM
- **Pydantic** - Data validation
- **psycopg2** - PostgreSQL adapter
- **IBM Bob MCP** - AI-powered schema analysis

### Frontend
- **React 18** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Build tool
- **TailwindCSS** - Utility-first CSS
- **Polling Service** - Custom React hook for drift monitoring

### Database
- **PostgreSQL 14+** - Primary database
- **Pagila** - Sample DVD rental database (21 tables)

---

## 📁 Project Structure

```
datacontractiq/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   │   ├── contracts.py  # Contract & drift endpoints
│   │   │   └── models.py     # Request/response models
│   │   ├── core/             # Core business logic
│   │   │   ├── drift_detector.py
│   │   │   ├── schema_introspector.py
│   │   │   ├── contract_formatter.py
│   │   │   └── contract_storage.py
│   │   ├── models/           # Data models
│   │   │   ├── contract.py
│   │   │   └── schema.py
│   │   ├── services/         # Service layer
│   │   │   ├── contract_service.py
│   │   │   └── drift_service.py
│   │   ├── db/               # Database connection
│   │   ├── config.py         # Configuration
│   │   └── main.py           # FastAPI app
│   ├── mcp_server.py         # MCP server integration
│   ├── requirements.txt
│   └── RULES.md              # Development guidelines
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Main app with drift monitoring
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.ts
├── data/
│   ├── contracts/            # Approved contracts (JSON + MD)
│   └── snapshots/            # Schema snapshots
├── docs/
│   ├── SETUP_GUIDE.md        # Detailed setup instructions
│   └── IBM_BOB_MCP_SETUP.md  # MCP configuration
├── skills/                   # Reusable development patterns
├── GreenCycleBikes/          # Sample Pagila database
└── README.md                 # This file
```

---

## 🔌 API Endpoints

### Contracts
- `GET /api/contracts` - List all contracts
- `GET /api/contracts/{id}` - Get contract details
- `POST /api/contracts/{id}/approve` - Approve contract
- `POST /api/contracts/{id}/answers` - Submit question answers

### Drift Detection
- `GET /api/drift/{table_name}` - Check drift for specific table
- `GET /api/drift/summary/all` - Get drift summary for all approved contracts

### Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)

---

## 🧪 Development

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality
```bash
# Backend linting
cd backend
pylint app/

# Frontend linting
cd frontend
npm run lint
```

### Database Configuration

Update `backend/app/config.py`:
```python
database_url: str = "postgresql://username@localhost:5432/pagila"
```

Or create `backend/.env`:
```
DATABASE_URL=postgresql://username@localhost:5432/pagila
```

---

## 📖 Documentation

- **[Setup Guide](docs/SETUP_GUIDE.md)** - Detailed installation and configuration
- **[MCP Setup](docs/IBM_BOB_MCP_SETUP.md)** - IBM Bob MCP server configuration
- **[Skills Library](skills/README.md)** - Reusable development patterns
- **[API Docs](http://localhost:8000/docs)** - Interactive API documentation

---

## 🎯 Use Cases

### Data Governance
- Maintain formal contracts for critical tables
- Track schema evolution over time
- Ensure compliance with data standards

### Change Management
- Detect unauthorized schema changes
- Prevent breaking changes in production
- Alert teams to contract violations

### Documentation
- Auto-generate human-readable schema docs
- Keep documentation in sync with database
- Capture business rules and relationships

### Team Collaboration
- Review and approve schema changes
- Answer clarification questions
- Track who approved what and when

---

## 🚧 Troubleshooting

### Drift Detection Not Working?
1. Verify backend is running: `curl http://localhost:8000/api/drift/summary/all`
2. Check database credentials in `backend/app/config.py`
3. Ensure contract is **approved** (draft contracts not monitored)
4. Wait full 30 seconds for next poll cycle
5. Check browser console for errors

### Database Connection Error?
```
FATAL: role "postgres" does not exist
```
**Solution**: Update `database_url` in `backend/app/config.py` with your actual PostgreSQL username.

### Frontend Not Showing Contracts?
1. Verify backend is running on port 8000
2. Check CORS settings in `backend/app/config.py`
3. Refresh browser and check network tab

---

## 🤝 Contributing

1. Follow the development guidelines in `backend/RULES.md`
2. Use the skills library for consistent patterns
3. Update documentation as you build
4. Test thoroughly before committing

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🏆 Acknowledgments

- **IBM Hackathon 2026** - Project inspiration
- **IBM Bob** - AI-powered schema analysis via MCP
- **Pagila Database** - Sample data for demos
- **FastAPI & React** - Modern web frameworks

---

## 📧 Contact

For questions or issues, please refer to the documentation or create an issue in the repository.

---

**Built with ❤️ for IBM Hackathon 2026**

*Empowering data teams with intelligent contract management and real-time drift detection*