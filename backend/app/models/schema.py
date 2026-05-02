"""
Schema data models for database introspection
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ConstraintType(str, Enum):
    """Types of database constraints"""
    PRIMARY_KEY = "primary_key"
    FOREIGN_KEY = "foreign_key"
    UNIQUE = "unique"
    CHECK = "check"
    NOT_NULL = "not_null"


class ColumnSchema(BaseModel):
    """Schema definition for a database column"""
    name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="Data type (e.g., integer, text, varchar)")
    nullable: bool = Field(default=True, description="Whether column allows NULL values")
    default_value: Optional[str] = Field(None, description="Default value expression")
    primary_key: bool = Field(default=False, description="Whether column is part of primary key")
    foreign_key: Optional[str] = Field(None, description="Referenced table.column if foreign key")
    unique: bool = Field(default=False, description="Whether column has unique constraint")
    auto_increment: bool = Field(default=False, description="Whether column auto-increments")
    max_length: Optional[int] = Field(None, description="Maximum length for string types")
    precision: Optional[int] = Field(None, description="Precision for numeric types")
    scale: Optional[int] = Field(None, description="Scale for numeric types")
    description: Optional[str] = Field(None, description="Column description/comment")


class ForeignKeyConstraint(BaseModel):
    """Foreign key relationship definition"""
    column_name: str = Field(..., description="Source column name")
    referenced_table: str = Field(..., description="Referenced table name")
    referenced_column: str = Field(..., description="Referenced column name")
    on_delete: Optional[str] = Field(None, description="ON DELETE action")
    on_update: Optional[str] = Field(None, description="ON UPDATE action")


class CheckConstraint(BaseModel):
    """Check constraint definition"""
    name: Optional[str] = Field(None, description="Constraint name")
    expression: str = Field(..., description="Check constraint expression")
    description: Optional[str] = Field(None, description="Business rule description")


class IndexSchema(BaseModel):
    """Index definition"""
    name: str = Field(..., description="Index name")
    columns: List[str] = Field(..., description="Indexed columns")
    unique: bool = Field(default=False, description="Whether index is unique")
    index_type: Optional[str] = Field(None, description="Index type (btree, hash, etc.)")


class TableSchema(BaseModel):
    """Complete schema definition for a database table"""
    table_name: str = Field(..., description="Table name")
    schema_name: str = Field(default="public", description="Schema/namespace name")
    columns: List[ColumnSchema] = Field(..., description="List of columns")
    primary_keys: List[str] = Field(default_factory=list, description="Primary key column names")
    foreign_keys: List[ForeignKeyConstraint] = Field(default_factory=list, description="Foreign key constraints")
    check_constraints: List[CheckConstraint] = Field(default_factory=list, description="Check constraints")
    unique_constraints: List[List[str]] = Field(default_factory=list, description="Unique constraint column groups")
    indexes: List[IndexSchema] = Field(default_factory=list, description="Table indexes")
    table_comment: Optional[str] = Field(None, description="Table description/comment")
    row_count: Optional[int] = Field(None, description="Approximate row count")


class CustomType(BaseModel):
    """Custom database type definition (e.g., ENUM, DOMAIN)"""
    type_name: str = Field(..., description="Type name")
    type_category: str = Field(..., description="Type category (enum, domain, composite)")
    values: Optional[List[str]] = Field(None, description="Enum values")
    base_type: Optional[str] = Field(None, description="Base type for domains")
    constraints: Optional[List[str]] = Field(None, description="Domain constraints")


class DatabaseSchema(BaseModel):
    """Complete database schema with all tables and types"""
    database_name: str = Field(..., description="Database name")
    tables: List[TableSchema] = Field(..., description="All tables in database")
    custom_types: List[CustomType] = Field(default_factory=list, description="Custom types (enums, domains)")
    total_tables: int = Field(..., description="Total number of tables")
    introspection_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When schema was captured")
    database_version: Optional[str] = Field(None, description="Database version")


class SchemaIntrospectionRequest(BaseModel):
    """Request to introspect a database schema"""
    source_type: str = Field(..., description="'file' or 'database'")
    source_path: Optional[str] = Field(None, description="Path to SQL file")
    connection_string: Optional[str] = Field(None, description="Database connection string")
    tables: Optional[List[str]] = Field(None, description="Specific tables to introspect (None = all)")


class SchemaIntrospectionResponse(BaseModel):
    """Response from schema introspection"""
    database_schema: DatabaseSchema = Field(..., description="Complete database schema")
    introspection_time_seconds: float = Field(..., description="Time taken to introspect")
    success: bool = Field(default=True, description="Whether introspection succeeded")
    message: Optional[str] = Field(None, description="Success or error message")


class SchemaSnapshot(BaseModel):
    """Snapshot of database schema at a point in time"""
    snapshot_id: str = Field(..., description="Unique snapshot identifier")
    database_schema: DatabaseSchema = Field(..., description="Schema at snapshot time")
    snapshot_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When snapshot was taken")
    snapshot_type: str = Field(default="manual", description="manual, scheduled, or pre-migration")
    notes: Optional[str] = Field(None, description="Notes about this snapshot")

# Made with Bob
