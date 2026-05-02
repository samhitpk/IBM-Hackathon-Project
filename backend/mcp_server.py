"""
DataContractIQ MCP Server
Exposes 7 tools for IBM Bob to generate and manage data contracts
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional
import time
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import our Phase 2 and Phase 3 modules
from app.core.sql_parser import parse_sql_file
from app.core.schema_introspector import introspect_database
from app.core.snapshot_manager import save_snapshot, list_snapshots
from app.core.contract_storage import (
    save_contract,
    load_contract,
    list_contracts,
    get_contract_by_table
)
from app.core.contract_formatter import contract_to_markdown
from app.core.drift_detector import detect_drift
from app.models.contract import (
    DataContract,
    ColumnContract,
    RelationshipContract,
    BusinessRule,
    ContractQuestion,
    ContractMetadata,
    ContractStatus
)
from app.models.schema import DatabaseSchema, TableSchema
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create MCP server instance
server = Server("datacontractiq")


# ============================================================================
# TOOL 1: introspect_schema
# ============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools for Bob"""
    return [
        Tool(
            name="introspect_schema",
            description="Read and analyze database schema from SQL file or live database. Returns complete schema metadata including tables, columns, constraints, and relationships.",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_type": {
                        "type": "string",
                        "enum": ["file", "database"],
                        "description": "Source to introspect: 'file' for SQL file, 'database' for live DB"
                    },
                    "source_path": {
                        "type": "string",
                        "description": "Path to SQL file (optional, uses default if not provided)"
                    },
                    "tables": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific tables to introspect (optional, default: all tables)"
                    }
                },
                "required": ["source_type"]
            }
        ),
        Tool(
            name="analyze_table",
            description="Deep analysis of a specific table's structure, relationships, and business rules. Includes sample data if requested.",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of table to analyze"
                    },
                    "include_sample_data": {
                        "type": "boolean",
                        "description": "Whether to include sample data rows",
                        "default": False
                    },
                    "max_samples": {
                        "type": "integer",
                        "description": "Number of sample rows to include",
                        "default": 10
                    }
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="generate_contract",
            description="Generate a plain English data contract for a table. Analyzes structure, infers business rules, and flags ambiguities for human review.",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Table to generate contract for"
                    },
                    "include_examples": {
                        "type": "boolean",
                        "description": "Whether to include example values",
                        "default": True
                    },
                    "format": {
                        "type": "string",
                        "enum": ["json", "markdown", "both"],
                        "description": "Output format",
                        "default": "both"
                    }
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="save_contract",
            description="Save an approved data contract to disk. Stores as JSON in data/contracts/ directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract": {
                        "type": "object",
                        "description": "Contract object to save (JSON format)"
                    },
                    "approved_by": {
                        "type": "string",
                        "description": "User who approved the contract (optional)"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Approval notes (optional)"
                    }
                },
                "required": ["contract"]
            }
        ),
        Tool(
            name="list_contracts",
            description="List all existing data contracts with optional filtering by status or table name.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["draft", "approved", "outdated", "archived"],
                        "description": "Filter by contract status (optional)"
                    },
                    "table_name": {
                        "type": "string",
                        "description": "Filter by table name (optional)"
                    }
                }
            }
        ),
        Tool(
            name="detect_drift",
            description="Compare current database schema against approved contract to detect changes. Classifies changes by severity and provides recommendations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Table to check for drift"
                    },
                    "contract_id": {
                        "type": "string",
                        "description": "Specific contract to compare against (optional, uses latest approved if not provided)"
                    }
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="compare_schemas",
            description="Compare two schema snapshots to see what changed between them. Useful for tracking schema evolution over time.",
            inputSchema={
                "type": "object",
                "properties": {
                    "snapshot_id_1": {
                        "type": "string",
                        "description": "First snapshot ID (baseline)"
                    },
                    "snapshot_id_2": {
                        "type": "string",
                        "description": "Second snapshot ID (optional, uses current schema if not provided)"
                    },
                    "table_name": {
                        "type": "string",
                        "description": "Specific table to compare (optional, compares all tables if not provided)"
                    }
                },
                "required": ["snapshot_id_1"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls from Bob"""
    
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    
    try:
        if name == "introspect_schema":
            return await handle_introspect_schema(arguments)
        elif name == "analyze_table":
            return await handle_analyze_table(arguments)
        elif name == "generate_contract":
            return await handle_generate_contract(arguments)
        elif name == "save_contract":
            return await handle_save_contract(arguments)
        elif name == "list_contracts":
            return await handle_list_contracts(arguments)
        elif name == "detect_drift":
            return await handle_detect_drift(arguments)
        elif name == "compare_schemas":
            return await handle_compare_schemas(arguments)
        else:
            return [TextContent(
                type="text",
                text=f"Error: Unknown tool '{name}'"
            )]
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


# ============================================================================
# Tool Handlers
# ============================================================================

async def handle_introspect_schema(args: Dict[str, Any]) -> list[TextContent]:
    """Handle introspect_schema tool call"""
    
    start_time = time.time()
    source_type = args.get("source_type")
    source_path = args.get("source_path")
    tables = args.get("tables")
    
    try:
        if source_type == "file":
            # Parse SQL file
            file_path = source_path or settings.sql_file_path
            logger.info(f"Parsing SQL file: {file_path}")
            
            db_schema = parse_sql_file(file_path)
            
            # Filter tables if specified
            if tables:
                db_schema.tables = [t for t in db_schema.tables if t.table_name in tables]
                db_schema.total_tables = len(db_schema.tables)
        
        else:  # database
            # Introspect live database
            logger.info("Introspecting live database")
            db_schema = introspect_database(schema="public", table_names=tables)
        
        elapsed = time.time() - start_time
        
        # Format response
        response = {
            "success": True,
            "database_name": db_schema.database_name,
            "total_tables": db_schema.total_tables,
            "tables": [t.table_name for t in db_schema.tables],
            "custom_types": [ct.type_name for ct in db_schema.custom_types],
            "introspection_time_seconds": round(elapsed, 3),
            "message": f"Successfully introspected {db_schema.total_tables} tables"
        }
        
        # Save snapshot for future reference
        snapshot = save_snapshot(db_schema, snapshot_type="manual", notes="Introspected via MCP")
        response["snapshot_id"] = snapshot.snapshot_id
        
        return [TextContent(
            type="text",
            text=json.dumps(response, indent=2)
        )]
    
    except Exception as e:
        logger.error(f"Introspection failed: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]


async def handle_analyze_table(args: Dict[str, Any]) -> list[TextContent]:
    """Handle analyze_table tool call"""
    
    table_name = args.get("table_name")
    if not table_name or not isinstance(table_name, str):
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "table_name is required and must be a string"
            }, indent=2)
        )]
    
    include_sample_data = args.get("include_sample_data", False)
    max_samples = args.get("max_samples", 10)
    
    try:
        # Introspect the specific table
        db_schema = introspect_database(schema="public", table_names=[table_name])
        
        if not db_schema.tables:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Table '{table_name}' not found"
                }, indent=2)
            )]
        
        table = db_schema.tables[0]
        
        # Build analysis
        analysis = {
            "success": True,
            "table_name": table.table_name,
            "schema_name": table.schema_name,
            "columns": [
                {
                    "name": col.name,
                    "type": col.data_type,
                    "nullable": col.nullable,
                    "default": col.default_value,
                    "primary_key": col.primary_key,
                    "foreign_key": col.foreign_key
                }
                for col in table.columns
            ],
            "primary_keys": table.primary_keys,
            "foreign_keys": [
                {
                    "column": fk.column_name,
                    "references": f"{fk.referenced_table}.{fk.referenced_column}",
                    "on_delete": fk.on_delete,
                    "on_update": fk.on_update
                }
                for fk in table.foreign_keys
            ],
            "row_count": table.row_count,
            "relationships": {
                "outgoing": len(table.foreign_keys),
                "incoming": 0  # Would need to query other tables
            }
        }
        
        # TODO: Add sample data if requested
        if include_sample_data:
            analysis["note"] = "Sample data feature coming soon"
        
        return [TextContent(
            type="text",
            text=json.dumps(analysis, indent=2)
        )]
    
    except Exception as e:
        logger.error(f"Table analysis failed: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]


async def handle_generate_contract(args: Dict[str, Any]) -> list[TextContent]:
    """Handle generate_contract tool call"""
    
    table_name = args.get("table_name")
    if not table_name or not isinstance(table_name, str):
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "table_name is required and must be a string"
            }, indent=2)
        )]
    
    include_examples = args.get("include_examples", True)
    output_format = args.get("format", "both")
    
    try:
        # Get table schema
        db_schema = introspect_database(schema="public", table_names=[table_name])
        
        if not db_schema.tables:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Table '{table_name}' not found"
                }, indent=2)
            )]
        
        table = db_schema.tables[0]
        
        # Generate contract (this is where Bob's intelligence comes in!)
        # For now, we create a basic contract structure that Bob can enhance
        contract = await _generate_contract_from_schema(table, include_examples)
        
        response = {
            "success": True,
            "table_name": table_name,
            "contract_id": contract.metadata.contract_id
        }
        
        if output_format in ["json", "both"]:
            response["contract_json"] = json.loads(contract.model_dump_json())
        
        if output_format in ["markdown", "both"]:
            response["contract_markdown"] = contract_to_markdown(contract)
        
        return [TextContent(
            type="text",
            text=json.dumps(response, indent=2) if output_format == "json" 
                 else response.get("contract_markdown", json.dumps(response, indent=2))
        )]
    
    except Exception as e:
        logger.error(f"Contract generation failed: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]


async def handle_save_contract(args: Dict[str, Any]) -> list[TextContent]:
    """Handle save_contract tool call"""
    
    contract_data = args.get("contract")
    if not contract_data or not isinstance(contract_data, dict):
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "contract is required and must be a valid object"
            }, indent=2)
        )]
    
    approved_by = args.get("approved_by")
    notes = args.get("notes")
    
    try:
        # Parse contract from JSON
        contract = DataContract(**contract_data)  # type: ignore
        
        # Save contract
        saved_contract = save_contract(contract, approved_by=approved_by, notes=notes)
        
        response = {
            "success": True,
            "contract_id": saved_contract.metadata.contract_id,
            "table_name": saved_contract.table_name,
            "status": saved_contract.metadata.status.value,
            "message": f"Contract saved successfully for table '{saved_contract.table_name}'"
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response, indent=2)
        )]
    
    except Exception as e:
        logger.error(f"Contract save failed: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]


async def handle_list_contracts(args: Dict[str, Any]) -> list[TextContent]:
    """Handle list_contracts tool call"""
    
    status_filter = args.get("status")
    table_name_filter = args.get("table_name")
    
    try:
        # Convert status string to enum if provided
        status_enum = None
        if status_filter:
            status_enum = ContractStatus(status_filter)
        
        # List contracts
        contracts = list_contracts(status=status_enum, table_name=table_name_filter)
        
        response = {
            "success": True,
            "total_contracts": len(contracts),
            "contracts": contracts
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response, indent=2)
        )]
    
    except Exception as e:
        logger.error(f"List contracts failed: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]


async def handle_detect_drift(args: Dict[str, Any]) -> list[TextContent]:
    """Handle detect_drift tool call"""
    
    table_name = args.get("table_name")
    if not table_name or not isinstance(table_name, str):
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "table_name is required and must be a string"
            }, indent=2)
        )]
    
    contract_id = args.get("contract_id")
    
    try:
        # Load contract
        if contract_id:
            contract = load_contract(contract_id)
        else:
            contract = get_contract_by_table(table_name, status=ContractStatus.APPROVED)
            if not contract:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": f"No approved contract found for table '{table_name}'"
                    }, indent=2)
                )]
        
        # Detect drift
        drift_report = detect_drift(table_name, contract=contract)
        
        response = {
            "success": True,
            "drift_detected": drift_report.drift_detected,
            "table_name": drift_report.table_name,
            "contract_id": drift_report.contract_id,
            "contract_version": drift_report.contract_version,
            "summary": drift_report.summary,
            "changes": [
                {
                    "type": change.change_type,
                    "column": change.column_name,
                    "severity": change.severity.value,
                    "description": change.description,
                    "impact": change.impact,
                    "recommendation": change.recommendation,
                    "breaking": change.breaking_change
                }
                for change in drift_report.changes
            ],
            "recommendations": drift_report.recommendations
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response, indent=2)
        )]
    
    except Exception as e:
        logger.error(f"Drift detection failed: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]


async def handle_compare_schemas(args: Dict[str, Any]) -> list[TextContent]:
    """Handle compare_schemas tool call"""
    
    snapshot_id_1 = args.get("snapshot_id_1")
    if not snapshot_id_1 or not isinstance(snapshot_id_1, str):
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "snapshot_id_1 is required and must be a string"
            }, indent=2)
        )]
    
    snapshot_id_2 = args.get("snapshot_id_2")
    table_name = args.get("table_name")
    
    try:
        # Load snapshots
        from app.core.snapshot_manager import load_snapshot
        
        snapshot1 = load_snapshot(snapshot_id_1)
        
        if snapshot_id_2:
            snapshot2 = load_snapshot(snapshot_id_2)
            snapshot2_id = snapshot2.snapshot_id
            snapshot2_timestamp = snapshot2.snapshot_timestamp.isoformat()
            snapshot2_tables = len(snapshot2.database_schema.tables)
        else:
            # Use current schema
            from datetime import datetime
            db_schema = introspect_database(schema="public")
            snapshot2_id = "current"
            snapshot2_timestamp = datetime.utcnow().isoformat()
            snapshot2_tables = len(db_schema.tables)
        
        # Compare schemas
        # For now, return basic comparison
        response = {
            "success": True,
            "snapshot_1": {
                "id": snapshot1.snapshot_id,
                "timestamp": snapshot1.snapshot_timestamp.isoformat(),
                "tables": len(snapshot1.database_schema.tables)
            },
            "snapshot_2": {
                "id": snapshot2_id,
                "timestamp": snapshot2_timestamp,
                "tables": snapshot2_tables
            },
            "note": "Detailed schema comparison coming soon"
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response, indent=2)
        )]
    
    except Exception as e:
        logger.error(f"Schema comparison failed: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
        )]


# ============================================================================
# Helper Functions
# ============================================================================

async def _generate_contract_from_schema(
    table: TableSchema,
    include_examples: bool
) -> DataContract:
    """
    Generate a basic contract from table schema.
    Bob will enhance this with better descriptions and business rules.
    """
    
    # Generate contract ID
    import uuid
    from datetime import datetime
    contract_id = f"{table.table_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    # Convert columns
    column_contracts = []
    for col in table.columns:
        column_contract = ColumnContract(
            name=col.name,
            description=f"Column {col.name} of type {col.data_type}",  # Bob will improve this
            data_type=col.data_type,
            nullable=col.nullable,
            constraints=[],
            default_value=col.default_value,
            business_rules=[],
            examples=[] if include_examples else [],
            valid_values=None,
            format=None,
            sensitivity=None
        )
        
        if col.primary_key:
            column_contract.constraints.append("PRIMARY KEY")
        if col.unique:
            column_contract.constraints.append("UNIQUE")
        if col.foreign_key:
            column_contract.constraints.append(f"FOREIGN KEY -> {col.foreign_key}")
        
        column_contracts.append(column_contract)
    
    # Convert relationships
    relationship_contracts = []
    for fk in table.foreign_keys:
        relationship_contract = RelationshipContract(
            type="foreign_key",
            column=fk.column_name,
            references_table=fk.referenced_table,
            references_column=fk.referenced_column,
            description=f"References {fk.referenced_table}.{fk.referenced_column}",
            on_delete=fk.on_delete,
            on_update=fk.on_update,
            cardinality="N:1"  # Default assumption
        )
        relationship_contracts.append(relationship_contract)
    
    # Create metadata
    metadata = ContractMetadata(
        contract_id=contract_id,
        version="1.0",
        status=ContractStatus.DRAFT,
        created_at=datetime.utcnow(),
        created_by="MCP Server",
        updated_at=None,
        updated_by=None,
        approved_at=None,
        approved_by=None,
        approval_notes=None,
        confidence_score=0.7  # Basic generation, Bob will improve
    )
    
    # Create contract
    contract = DataContract(
        table_name=table.table_name,
        schema_name=table.schema_name,
        description=f"Table {table.table_name}",  # Bob will improve this
        purpose=f"Stores data for {table.table_name}",  # Bob will improve this
        columns=column_contracts,
        primary_keys=table.primary_keys,
        relationships=relationship_contracts,
        business_rules=[],
        data_quality_rules=[],
        questions=[],  # Bob will add questions for ambiguities
        metadata=metadata,
        row_count=table.row_count,
        data_retention=None,
        access_control=None,
        update_frequency=None,
        notes=None
    )
    
    return contract


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Run the MCP server"""
    logger.info("Starting DataContractIQ MCP Server...")
    logger.info(f"Database: {settings.database_url}")
    logger.info(f"Contracts directory: {settings.contracts_dir}")
    logger.info(f"Snapshots directory: {settings.snapshots_dir}")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())


# Made with Bob