"""
Schema API endpoints for database introspection
Provides REST API for schema extraction from SQL files or live databases
"""
from fastapi import APIRouter, HTTPException, status
from typing import Optional
import time
import logging
import os

from app.models.schema import (
    SchemaIntrospectionRequest,
    SchemaIntrospectionResponse,
    DatabaseSchema
)
from app.core.sql_parser import parse_sql_file
from app.core.schema_introspector import introspect_database
from app.core.snapshot_manager import save_snapshot, list_snapshots, load_snapshot
from app.config import settings

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter()


@router.post("/introspect", response_model=SchemaIntrospectionResponse)
async def introspect_schema(request: SchemaIntrospectionRequest):
    """
    Introspect database schema from SQL file or live database.
    
    **Source Types:**
    - `file`: Parse schema from SQL DDL file
    - `database`: Introspect live database connection
    
    **Request Body:**
    ```json
    {
        "source_type": "file",
        "source_path": "/path/to/schema.sql",
        "tables": ["table1", "table2"]  // optional
    }
    ```
    
    **Response:**
    - Complete database schema with all tables, columns, constraints
    - Introspection time in seconds
    - Success status and message
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/schema/introspect" \\
         -H "Content-Type: application/json" \\
         -d '{"source_type": "file", "source_path": "pagila-insert-data.sql"}'
    ```
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting schema introspection: {request.source_type}")
        
        # Validate source type
        if request.source_type not in ["file", "database"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="source_type must be 'file' or 'database'"
            )
        
        # Introspect based on source type
        if request.source_type == "file":
            database_schema = await _introspect_from_file(request)
        else:
            database_schema = await _introspect_from_database(request)
        
        # Calculate introspection time
        introspection_time = time.time() - start_time
        
        logger.info(
            f"Introspection complete: {database_schema.total_tables} tables "
            f"in {introspection_time:.2f}s"
        )
        
        # Return response
        return SchemaIntrospectionResponse(
            database_schema=database_schema,
            introspection_time_seconds=round(introspection_time, 3),
            success=True,
            message=f"Successfully introspected {database_schema.total_tables} tables"
        )
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Introspection failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Introspection failed: {str(e)}"
        )


async def _introspect_from_file(request: SchemaIntrospectionRequest) -> DatabaseSchema:
    """
    Introspect schema from SQL file.
    
    Args:
        request: Introspection request with file path
        
    Returns:
        DatabaseSchema: Parsed database schema
    """
    if not request.source_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="source_path is required for file introspection"
        )
    
    # Resolve file path (handle relative paths)
    file_path = request.source_path
    
    # If path is relative, try to resolve from project root
    if not os.path.isabs(file_path):
        # Try config path first
        if hasattr(settings, 'sql_file_path') and settings.sql_file_path:
            file_path = settings.sql_file_path
        else:
            # Try relative to current directory
            file_path = os.path.abspath(file_path)
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"SQL file not found: {file_path}")
    
    logger.info(f"Parsing SQL file: {file_path}")
    
    # Parse SQL file
    database_schema = parse_sql_file(file_path)
    
    # Filter tables if specified
    if request.tables:
        database_schema.tables = [
            table for table in database_schema.tables
            if table.table_name in request.tables
        ]
        database_schema.total_tables = len(database_schema.tables)
    
    return database_schema


async def _introspect_from_database(request: SchemaIntrospectionRequest) -> DatabaseSchema:
    """
    Introspect schema from live database.
    
    Args:
        request: Introspection request with optional connection string
        
    Returns:
        DatabaseSchema: Introspected database schema
    """
    # Use connection string from request or default from settings
    connection_string = request.connection_string or settings.database_url
    
    logger.info(f"Introspecting live database")
    
    # Introspect database (uses default engine from settings)
    database_schema = introspect_database(
        schema="public",
        table_names=request.tables
    )
    
    return database_schema


@router.post("/introspect/snapshot", response_model=dict)
async def introspect_and_snapshot(
    request: SchemaIntrospectionRequest,
    snapshot_type: str = "manual",
    notes: Optional[str] = None
):
    """
    Introspect database schema and save as snapshot.
    
    Combines introspection and snapshot creation in one operation.
    Useful for creating baseline snapshots or scheduled backups.
    
    **Query Parameters:**
    - `snapshot_type`: Type of snapshot (manual, scheduled, pre-migration)
    - `notes`: Optional notes about this snapshot
    
    **Response:**
    ```json
    {
        "snapshot_id": "pagila_20260501_203622_a1b2c3d4",
        "database_name": "Pagila",
        "total_tables": 21,
        "introspection_time_seconds": 2.345,
        "message": "Schema introspected and snapshot saved"
    }
    ```
    """
    try:
        # Introspect schema
        introspection_response = await introspect_schema(request)
        
        if not introspection_response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Introspection failed"
            )
        
        # Save snapshot
        snapshot = save_snapshot(
            database_schema=introspection_response.database_schema,
            snapshot_type=snapshot_type,
            notes=notes
        )
        
        logger.info(f"Created snapshot: {snapshot.snapshot_id}")
        
        return {
            "snapshot_id": snapshot.snapshot_id,
            "database_name": snapshot.database_schema.database_name,
            "total_tables": snapshot.database_schema.total_tables,
            "introspection_time_seconds": introspection_response.introspection_time_seconds,
            "snapshot_timestamp": snapshot.snapshot_timestamp.isoformat(),
            "message": "Schema introspected and snapshot saved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create snapshot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create snapshot: {str(e)}"
        )


@router.get("/snapshots", response_model=dict)
async def get_snapshots():
    """
    List all available schema snapshots.
    
    **Response:**
    ```json
    {
        "snapshots": [
            {
                "snapshot_id": "pagila_20260501_203622_a1b2c3d4",
                "database_name": "Pagila",
                "snapshot_timestamp": "2026-05-01T20:36:22",
                "snapshot_type": "manual",
                "total_tables": 21,
                "notes": "Initial baseline"
            }
        ],
        "total_count": 1
    }
    ```
    """
    try:
        snapshots = list_snapshots()
        
        return {
            "snapshots": snapshots,
            "total_count": len(snapshots)
        }
        
    except Exception as e:
        logger.error(f"Failed to list snapshots: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list snapshots: {str(e)}"
        )


@router.get("/snapshots/{snapshot_id}", response_model=dict)
async def get_snapshot(snapshot_id: str):
    """
    Get a specific schema snapshot by ID.
    
    **Path Parameters:**
    - `snapshot_id`: Unique snapshot identifier
    
    **Response:**
    - Complete snapshot with full database schema
    """
    try:
        snapshot = load_snapshot(snapshot_id)
        
        return {
            "snapshot_id": snapshot.snapshot_id,
            "database_name": snapshot.database_schema.database_name,
            "snapshot_timestamp": snapshot.snapshot_timestamp.isoformat(),
            "snapshot_type": snapshot.snapshot_type,
            "notes": snapshot.notes,
            "database_schema": snapshot.database_schema.model_dump()
        }
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot not found: {snapshot_id}"
        )
    except Exception as e:
        logger.error(f"Failed to load snapshot {snapshot_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load snapshot: {str(e)}"
        )


@router.get("/health", response_model=dict)
async def schema_health_check():
    """
    Health check for schema introspection service.
    
    Verifies:
    - SQL file accessibility
    - Database connectivity
    - Snapshots directory
    
    **Response:**
    ```json
    {
        "status": "healthy",
        "sql_file_accessible": true,
        "database_connected": true,
        "snapshots_directory": "/path/to/snapshots",
        "available_snapshots": 5
    }
    ```
    """
    from app.db.database import test_connection
    
    health_status = {
        "status": "healthy",
        "sql_file_accessible": False,
        "database_connected": False,
        "snapshots_directory": str(settings.snapshots_dir),
        "available_snapshots": 0
    }
    
    # Check SQL file
    try:
        if hasattr(settings, 'sql_file_path') and settings.sql_file_path:
            health_status["sql_file_accessible"] = os.path.exists(settings.sql_file_path)
    except Exception as e:
        logger.warning(f"Could not check SQL file: {e}")
    
    # Check database connection
    try:
        health_status["database_connected"] = test_connection()
    except Exception as e:
        logger.warning(f"Database connection check failed: {e}")
    
    # Check snapshots
    try:
        snapshots = list_snapshots()
        health_status["available_snapshots"] = len(snapshots)
    except Exception as e:
        logger.warning(f"Could not list snapshots: {e}")
    
    # Determine overall status
    if not health_status["database_connected"]:
        health_status["status"] = "degraded"
    
    return health_status


# Made with Bob