# Skill: FastAPI Backend Development

## Purpose
Build RESTful API endpoints for DataContractIQ using FastAPI with proper structure, validation, and error handling.

## When to Use
- Creating new API endpoints
- Implementing request/response models
- Adding validation logic
- Handling errors gracefully

## Process

### 1. Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Configuration management
│   ├── dependencies.py      # Shared dependencies
│   ├── api/
│   │   ├── __init__.py
│   │   ├── contracts.py     # Contract endpoints
│   │   ├── schema.py        # Schema endpoints
│   │   ├── drift.py         # Drift detection endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── schema_parser.py
│   │   ├── bob_engine.py
│   │   ├── drift_detector.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schema.py        # Pydantic models
│   │   ├── contract.py
│   │   ├── alert.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py       # Database session
│   │   ├── models.py        # SQLAlchemy models
```

### 2. FastAPI Application Setup

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import contracts, schema, drift

app = FastAPI(
    title="DataContractIQ API",
    description="AI-powered data contract generation and drift detection",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(contracts.router, prefix="/api/contracts", tags=["contracts"])
app.include_router(schema.router, prefix="/api/schema", tags=["schema"])
app.include_router(drift.router, prefix="/api/drift", tags=["drift"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 3. Pydantic Models for Validation

```python
# app/models/schema.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ColumnSchema(BaseModel):
    name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="Data type")
    nullable: bool = Field(default=True)
    default_value: Optional[str] = None
    primary_key: bool = Field(default=False)
    foreign_key: Optional[str] = None
    description: Optional[str] = None

class TableSchema(BaseModel):
    table_name: str
    columns: List[ColumnSchema]
    primary_keys: List[str]
    foreign_keys: List[dict]
    constraints: List[dict]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SchemaIntrospectionRequest(BaseModel):
    source_type: str = Field(..., description="'file' or 'database'")
    source_path: Optional[str] = None
    connection_string: Optional[str] = None

class SchemaIntrospectionResponse(BaseModel):
    tables: List[TableSchema]
    total_tables: int
    introspection_time: float
```

### 4. API Endpoint Implementation

```python
# app/api/schema.py
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.models.schema import (
    SchemaIntrospectionRequest,
    SchemaIntrospectionResponse,
    TableSchema
)
from app.core.schema_parser import SchemaParser
import time

router = APIRouter()

@router.post("/introspect", response_model=SchemaIntrospectionResponse)
async def introspect_schema(request: SchemaIntrospectionRequest):
    """
    Introspect database schema from file or live connection.
    
    - **source_type**: 'file' or 'database'
    - **source_path**: Path to SQL file (if source_type='file')
    - **connection_string**: Database connection (if source_type='database')
    """
    start_time = time.time()
    
    try:
        parser = SchemaParser()
        
        if request.source_type == "file":
            if not request.source_path:
                raise HTTPException(400, "source_path required for file source")
            tables = await parser.parse_sql_file(request.source_path)
            
        elif request.source_type == "database":
            if not request.connection_string:
                raise HTTPException(400, "connection_string required for database source")
            tables = await parser.introspect_database(request.connection_string)
            
        else:
            raise HTTPException(400, f"Invalid source_type: {request.source_type}")
        
        introspection_time = time.time() - start_time
        
        return SchemaIntrospectionResponse(
            tables=tables,
            total_tables=len(tables),
            introspection_time=introspection_time
        )
        
    except FileNotFoundError:
        raise HTTPException(404, "SQL file not found")
    except Exception as e:
        raise HTTPException(500, f"Introspection failed: {str(e)}")

@router.get("/tables", response_model=List[str])
async def list_tables():
    """List all available tables in the schema."""
    try:
        # Implementation
        return ["film", "customer", "rental", "payment"]
    except Exception as e:
        raise HTTPException(500, f"Failed to list tables: {str(e)}")

@router.get("/tables/{table_name}", response_model=TableSchema)
async def get_table_schema(table_name: str):
    """Get detailed schema for a specific table."""
    try:
        # Implementation
        pass
    except Exception as e:
        raise HTTPException(404, f"Table not found: {table_name}")
```

### 5. Contract Generation Endpoints

```python
# app/api/contracts.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.contract import (
    ContractGenerationRequest,
    ContractGenerationResponse,
    Contract,
    ContractApproval
)
from app.core.bob_engine import BobEngine

router = APIRouter()

@router.post("/generate", response_model=ContractGenerationResponse)
async def generate_contract(
    request: ContractGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate data contract using IBM Bob.
    
    - **table_name**: Name of table to generate contract for
    - **include_sample_data**: Whether to analyze sample data
    - **batch_mode**: Generate for multiple tables
    """
    try:
        bob = BobEngine()
        
        # Generate contract using Bob
        contract = await bob.generate_contract(
            table_name=request.table_name,
            schema_metadata=request.schema_metadata,
            include_sample_data=request.include_sample_data
        )
        
        # Save draft contract
        contract_id = await save_draft_contract(contract)
        
        return ContractGenerationResponse(
            contract_id=contract_id,
            contract=contract,
            questions=contract.questions,
            status="draft"
        )
        
    except Exception as e:
        raise HTTPException(500, f"Contract generation failed: {str(e)}")

@router.get("/{contract_id}", response_model=Contract)
async def get_contract(contract_id: str):
    """Retrieve a specific contract by ID."""
    try:
        contract = await load_contract(contract_id)
        if not contract:
            raise HTTPException(404, f"Contract not found: {contract_id}")
        return contract
    except Exception as e:
        raise HTTPException(500, str(e))

@router.put("/{contract_id}", response_model=Contract)
async def update_contract(contract_id: str, contract: Contract):
    """Update a contract (during review)."""
    try:
        updated = await save_contract(contract_id, contract)
        return updated
    except Exception as e:
        raise HTTPException(500, f"Update failed: {str(e)}")

@router.post("/{contract_id}/approve", response_model=Contract)
async def approve_contract(contract_id: str, approval: ContractApproval):
    """Approve a contract and make it active."""
    try:
        contract = await load_contract(contract_id)
        contract.status = "approved"
        contract.approved_by = approval.approver
        contract.approved_at = datetime.utcnow()
        
        await save_contract(contract_id, contract)
        return contract
    except Exception as e:
        raise HTTPException(500, f"Approval failed: {str(e)}")
```

### 6. Drift Detection Endpoints

```python
# app/api/drift.py
from fastapi import APIRouter, HTTPException
from app.models.alert import DriftAlert, DriftDetectionRequest
from app.core.drift_detector import DriftDetector

router = APIRouter()

@router.post("/detect", response_model=List[DriftAlert])
async def detect_drift(request: DriftDetectionRequest):
    """
    Detect schema drift against approved contract.
    
    - **table_name**: Table to check
    - **contract_id**: Approved contract to compare against
    """
    try:
        detector = DriftDetector()
        
        # Get current schema
        current_schema = await get_current_schema(request.table_name)
        
        # Load approved contract
        contract = await load_contract(request.contract_id)
        
        # Detect changes
        alerts = await detector.detect_changes(
            current_schema=current_schema,
            approved_contract=contract,
            use_bob_analysis=True
        )
        
        # Save alerts
        for alert in alerts:
            await save_alert(alert)
        
        return alerts
        
    except Exception as e:
        raise HTTPException(500, f"Drift detection failed: {str(e)}")

@router.get("/alerts", response_model=List[DriftAlert])
async def get_alerts(
    severity: Optional[str] = None,
    table_name: Optional[str] = None,
    limit: int = 50
):
    """Get drift alerts with optional filtering."""
    try:
        alerts = await load_alerts(
            severity=severity,
            table_name=table_name,
            limit=limit
        )
        return alerts
    except Exception as e:
        raise HTTPException(500, str(e))

@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Mark an alert as acknowledged."""
    try:
        await update_alert_status(alert_id, "acknowledged")
        return {"status": "acknowledged"}
    except Exception as e:
        raise HTTPException(500, str(e))
```

### 7. Error Handling

```python
# app/main.py
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

### 8. Dependency Injection

```python
# app/dependencies.py
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Authentication logic
    pass

async def get_db_session() -> Session:
    db = get_db()
    try:
        yield db
    finally:
        db.close()
```

## Testing Endpoints

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_introspect_schema():
    response = client.post("/api/schema/introspect", json={
        "source_type": "file",
        "source_path": "pagila-insert-data.sql"
    })
    assert response.status_code == 200
    assert "tables" in response.json()
```

## Best Practices

- Use Pydantic models for request/response validation
- Implement proper error handling with HTTPException
- Use async/await for I/O operations
- Add comprehensive docstrings for API documentation
- Use dependency injection for shared resources
- Implement rate limiting for production
- Add authentication/authorization
- Log all API requests and errors
- Use background tasks for long-running operations

## Integration with Other Skills
- Uses **SCHEMA_ANALYSIS** for introspection
- Calls **CONTRACT_GENERATION** for Bob integration
- Implements **DRIFT_DETECTION** endpoints
- Provides data for frontend components