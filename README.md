# DataContractIQ

AI-powered data contract generation and drift detection tool using IBM Bob for context-aware analysis.

## Overview

DataContractIQ automatically analyzes existing database schemas, extracts implicit business rules, and generates formal human-readable data contracts. It continuously monitors for schema drift and provides intelligent impact analysis.

### Key Features

- **Stage 1 - Contract Generation**: AI-powered analysis of database schemas to generate comprehensive data contracts
- **Stage 2 - Human Review**: Interactive interface for reviewing and approving contracts with targeted questions
- **Stage 3 - Drift Detection**: Continuous monitoring for schema changes with intelligent impact analysis

### Why IBM Bob?

- **Full Context Awareness**: Reads entire database schemas without token limits
- **Workspace Integration**: Direct access to database files and documentation
- **Cross-Table Intelligence**: Understands relationships across all tables simultaneously
- **Iterative Refinement**: Can be asked follow-up questions for clarification

## Project Structure

```
datacontractiq/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core business logic
│   │   ├── models/      # Data models
│   │   └── main.py      # Application entry point
│   └── requirements.txt
├── frontend/            # React + TypeScript frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   └── App.tsx      # Main app component
│   └── package.json
├── data/
│   ├── contracts/       # Approved contracts
│   └── snapshots/       # Schema snapshots
├── docs/
│   ├── SETUP_GUIDE.md   # Detailed setup instructions
│   └── IMPLEMENTATION_PLAN.md
├── skills/              # Reusable instruction sets
└── GreenCycleBikes/     # Sample Pagila database
```

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- PostgreSQL 14+

### Setup

**Detailed setup instructions are in [`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md)**

Quick commands:

```powershell
# Backend
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# Frontend (in new terminal)
cd frontend
npm install
npm run dev

# Database
psql -U postgres
CREATE DATABASE pagila;
\q
psql -U postgres -d pagila -f GreenCycleBikes/pagila-master/pagila-insert-data.sql
```

### Access

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Technology Stack

**Backend:**
- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL

**Frontend:**
- React 18+
- TypeScript
- Vite
- TailwindCSS

**AI:**
- IBM Bob (context-aware AI assistant)

## Implementation Phases

- [x] **Phase 1**: Project Foundation & Database Setup
- [ ] **Phase 2**: Schema Introspection Engine
- [ ] **Phase 3**: AI Contract Generation (Stage 1)
- [ ] **Phase 4**: Review Interface (Stage 2)
- [ ] **Phase 5**: Drift Detection System (Stage 3)
- [ ] **Phase 6**: Demo Integration & Testing

## Documentation

- [Setup Guide](docs/SETUP_GUIDE.md) - Detailed installation and configuration
- [Implementation Plan](IMPLEMENTATION_PLAN.md) - Phase-by-phase development plan
- [Skills Library](skills/README.md) - Reusable development patterns

## Demo Database

The project uses the **Pagila** database (DVD rental system) with 21 tables including:
- film, actor, customer, rental, payment
- address, city, country, language
- inventory, store, staff

## Development

### Running Tests

```powershell
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality

```powershell
# Backend linting
cd backend
pylint app/

# Frontend linting
cd frontend
npm run lint
```

## Contributing

1. Follow the implementation plan phases
2. Use the skills library for consistent patterns
3. Update documentation as you build
4. Test thoroughly before moving to next phase

## License

MIT License - See LICENSE file for details

## Contact

For questions or issues, please refer to the documentation or create an issue.

---

*Built for IBM Hackathon 2026*