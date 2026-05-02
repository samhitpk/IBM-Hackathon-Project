"""
Schema Introspector for live database introspection using SQLAlchemy
Extracts complete schema metadata from a running PostgreSQL database
"""
from sqlalchemy import inspect, text
from sqlalchemy.engine import Inspector, Engine
from typing import List, Dict, Optional, Any
import logging

from app.db.database import engine, get_inspector, get_database_version
from app.models.schema import (
    TableSchema,
    ColumnSchema,
    ForeignKeyConstraint,
    CheckConstraint,
    IndexSchema,
    CustomType,
    DatabaseSchema
)

logger = logging.getLogger(__name__)


class SchemaIntrospector:
    """Introspect live database schema using SQLAlchemy Inspector"""
    
    def __init__(self, db_engine: Optional[Engine] = None):
        """
        Initialize introspector with database engine.
        
        Args:
            db_engine: SQLAlchemy engine (uses default if None)
        """
        self.engine = db_engine or engine
        self.inspector: Inspector = inspect(self.engine)
        
    def introspect_database(
        self,
        schema: str = "public",
        table_names: Optional[List[str]] = None
    ) -> DatabaseSchema:
        """
        Introspect complete database schema.
        
        Args:
            schema: Database schema name (default: "public")
            table_names: Specific tables to introspect (None = all tables)
            
        Returns:
            DatabaseSchema: Complete database schema metadata
        """
        logger.info(f"Introspecting database schema: {schema}")
        
        # Get all table names if not specified
        if table_names is None:
            table_names = self.inspector.get_table_names(schema=schema)
        
        logger.info(f"Found {len(table_names)} tables to introspect")
        
        # Introspect each table
        tables = []
        for table_name in table_names:
            try:
                table_schema = self._introspect_table(table_name, schema)
                tables.append(table_schema)
                logger.debug(f"Introspected table: {table_name}")
            except Exception as e:
                logger.error(f"Error introspecting table {table_name}: {e}")
        
        # Get custom types
        custom_types = self._introspect_custom_types(schema)
        
        # Get database version
        db_version = get_database_version()
        
        # Extract database name from connection
        db_name = self._get_database_name()
        
        database_schema = DatabaseSchema(
            database_name=db_name,
            tables=tables,
            custom_types=custom_types,
            total_tables=len(tables),
            database_version=db_version
        )
        
        logger.info(f"Introspection complete: {len(tables)} tables, {len(custom_types)} custom types")
        return database_schema
    
    def _introspect_table(self, table_name: str, schema: str) -> TableSchema:
        """
        Introspect a single table.
        
        Args:
            table_name: Name of the table
            schema: Schema name
            
        Returns:
            TableSchema: Complete table schema metadata
        """
        # Get columns
        columns = self._introspect_columns(table_name, schema)
        
        # Get primary keys
        primary_keys = self._introspect_primary_keys(table_name, schema)
        
        # Get foreign keys
        foreign_keys = self._introspect_foreign_keys(table_name, schema)
        
        # Get check constraints
        check_constraints = self._introspect_check_constraints(table_name, schema)
        
        # Get unique constraints
        unique_constraints = self._introspect_unique_constraints(table_name, schema)
        
        # Get indexes
        indexes = self._introspect_indexes(table_name, schema)
        
        # Get table comment
        table_comment = self._get_table_comment(table_name, schema)
        
        # Get approximate row count
        row_count = self._get_row_count(table_name, schema)
        
        # Mark primary key columns
        for column in columns:
            if column.name in primary_keys:
                column.primary_key = True
        
        # Mark foreign key columns
        for fk in foreign_keys:
            for column in columns:
                if column.name == fk.column_name:
                    column.foreign_key = f"{fk.referenced_table}.{fk.referenced_column}"
        
        table_schema = TableSchema(
            table_name=table_name,
            schema_name=schema,
            columns=columns,
            primary_keys=primary_keys,
            foreign_keys=foreign_keys,
            check_constraints=check_constraints,
            unique_constraints=unique_constraints,
            indexes=indexes,
            table_comment=table_comment,
            row_count=row_count
        )
        
        return table_schema
    
    def _introspect_columns(self, table_name: str, schema: str) -> List[ColumnSchema]:
        """Introspect table columns"""
        columns = []
        
        for col in self.inspector.get_columns(table_name, schema=schema):
            # Extract column metadata
            column_name = col['name']
            data_type = str(col['type'])
            nullable = col['nullable']
            default_value = str(col['default']) if col['default'] is not None else None
            
            # Check for auto-increment (serial/sequence)
            auto_increment = False
            if default_value and 'nextval' in default_value.lower():
                auto_increment = True
            
            # Extract type parameters
            max_length = None
            precision = None
            scale = None
            
            # Try to get length/precision from type
            type_obj = col['type']
            if hasattr(type_obj, 'length'):
                length_val = getattr(type_obj, 'length', None)
                if length_val:
                    max_length = length_val
            if hasattr(type_obj, 'precision'):
                precision_val = getattr(type_obj, 'precision', None)
                if precision_val:
                    precision = precision_val
            if hasattr(type_obj, 'scale'):
                scale_val = getattr(type_obj, 'scale', None)
                if scale_val:
                    scale = scale_val
            
            # Get column comment
            comment = col.get('comment')
            
            column_schema = ColumnSchema(
                name=column_name,
                data_type=data_type,
                nullable=nullable,
                default_value=default_value,
                primary_key=False,  # Will be set later
                foreign_key=None,   # Will be set later
                unique=False,       # Will be determined from constraints
                auto_increment=auto_increment,
                max_length=max_length,
                precision=precision,
                scale=scale,
                description=comment
            )
            
            columns.append(column_schema)
        
        return columns
    
    def _introspect_primary_keys(self, table_name: str, schema: str) -> List[str]:
        """Introspect primary key columns"""
        pk_constraint = self.inspector.get_pk_constraint(table_name, schema=schema)
        return pk_constraint.get('constrained_columns', [])
    
    def _introspect_foreign_keys(self, table_name: str, schema: str) -> List[ForeignKeyConstraint]:
        """Introspect foreign key constraints"""
        foreign_keys = []
        
        for fk in self.inspector.get_foreign_keys(table_name, schema=schema):
            # Handle single and multi-column foreign keys
            constrained_columns = fk['constrained_columns']
            referred_columns = fk['referred_columns']
            
            # Create ForeignKeyConstraint for each column pair
            for col, ref_col in zip(constrained_columns, referred_columns):
                fk_constraint = ForeignKeyConstraint(
                    column_name=col,
                    referenced_table=fk['referred_table'],
                    referenced_column=ref_col,
                    on_delete=fk.get('ondelete'),
                    on_update=fk.get('onupdate')
                )
                foreign_keys.append(fk_constraint)
        
        return foreign_keys
    
    def _introspect_check_constraints(self, table_name: str, schema: str) -> List[CheckConstraint]:
        """Introspect check constraints"""
        check_constraints = []
        
        try:
            for check in self.inspector.get_check_constraints(table_name, schema=schema):
                check_constraint = CheckConstraint(
                    name=check.get('name'),
                    expression=check.get('sqltext', ''),
                    description=None
                )
                check_constraints.append(check_constraint)
        except NotImplementedError:
            # Some dialects don't support check constraint introspection
            logger.debug(f"Check constraint introspection not supported for {table_name}")
        
        return check_constraints
    
    def _introspect_unique_constraints(self, table_name: str, schema: str) -> List[List[str]]:
        """Introspect unique constraints"""
        unique_constraints = []
        
        for unique in self.inspector.get_unique_constraints(table_name, schema=schema):
            columns = unique.get('column_names', [])
            if columns:
                unique_constraints.append(columns)
        
        return unique_constraints
    
    def _introspect_indexes(self, table_name: str, schema: str) -> List[IndexSchema]:
        """Introspect table indexes"""
        indexes = []
        
        for idx in self.inspector.get_indexes(table_name, schema=schema):
            # Skip indexes without names or columns
            idx_name = idx.get('name')
            idx_columns = idx.get('column_names')
            
            if not idx_name or not idx_columns:
                continue
                
            index_schema = IndexSchema(
                name=idx_name,
                columns=[col for col in idx_columns if col],  # Filter out None values
                unique=idx.get('unique', False),
                index_type=idx.get('type')
            )
            indexes.append(index_schema)
        
        return indexes
    
    def _introspect_custom_types(self, schema: str) -> List[CustomType]:
        """
        Introspect custom types (ENUMs, DOMAINs) from database.
        Uses direct SQL queries to PostgreSQL system catalogs.
        """
        custom_types = []
        
        try:
            with self.engine.connect() as conn:
                # Query for ENUM types
                enum_query = text("""
                    SELECT t.typname as type_name, 
                           array_agg(e.enumlabel ORDER BY e.enumsortorder) as enum_values
                    FROM pg_type t
                    JOIN pg_enum e ON t.oid = e.enumtypid
                    JOIN pg_namespace n ON t.typnamespace = n.oid
                    WHERE n.nspname = :schema
                    GROUP BY t.typname
                """)
                
                result = conn.execute(enum_query, {"schema": schema})
                for row in result:
                    custom_type = CustomType(
                        type_name=row.type_name,
                        type_category="enum",
                        values=list(row.enum_values),
                        base_type=None,
                        constraints=None
                    )
                    custom_types.append(custom_type)
                
                # Query for DOMAIN types
                domain_query = text("""
                    SELECT t.typname as type_name,
                           pg_catalog.format_type(t.typbasetype, t.typtypmod) as base_type,
                           pg_catalog.pg_get_constraintdef(c.oid, true) as constraint_def
                    FROM pg_type t
                    JOIN pg_namespace n ON t.typnamespace = n.oid
                    LEFT JOIN pg_constraint c ON c.contypid = t.oid
                    WHERE t.typtype = 'd' AND n.nspname = :schema
                """)
                
                result = conn.execute(domain_query, {"schema": schema})
                for row in result:
                    constraints = [row.constraint_def] if row.constraint_def else None
                    custom_type = CustomType(
                        type_name=row.type_name,
                        type_category="domain",
                        base_type=row.base_type,
                        constraints=constraints,
                        values=None
                    )
                    custom_types.append(custom_type)
                    
        except Exception as e:
            logger.error(f"Error introspecting custom types: {e}")
        
        return custom_types
    
    def _get_table_comment(self, table_name: str, schema: str) -> Optional[str]:
        """Get table comment/description"""
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT obj_description(c.oid, 'pg_class') as comment
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE c.relname = :table_name AND n.nspname = :schema
                """)
                result = conn.execute(query, {"table_name": table_name, "schema": schema})
                row = result.first()
                return row.comment if row and row.comment else None
        except Exception as e:
            logger.debug(f"Could not get comment for {table_name}: {e}")
            return None
    
    def _get_row_count(self, table_name: str, schema: str) -> Optional[int]:
        """Get approximate row count for table"""
        try:
            with self.engine.connect() as conn:
                # Use pg_class for fast approximate count
                query = text("""
                    SELECT reltuples::bigint as row_count
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE c.relname = :table_name AND n.nspname = :schema
                """)
                result = conn.execute(query, {"table_name": table_name, "schema": schema})
                row = result.first()
                return int(row.row_count) if row and row.row_count else None
        except Exception as e:
            logger.debug(f"Could not get row count for {table_name}: {e}")
            return None
    
    def _get_database_name(self) -> str:
        """Extract database name from connection"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT current_database()"))
                db_name = result.scalar()
                return db_name if db_name else "Unknown"
        except Exception as e:
            logger.error(f"Could not get database name: {e}")
            return "Unknown"


def introspect_database(
    schema: str = "public",
    table_names: Optional[List[str]] = None,
    db_engine: Optional[Engine] = None
) -> DatabaseSchema:
    """
    Convenience function to introspect database schema.
    
    Args:
        schema: Database schema name (default: "public")
        table_names: Specific tables to introspect (None = all)
        db_engine: SQLAlchemy engine (uses default if None)
        
    Returns:
        DatabaseSchema: Complete database schema metadata
    """
    introspector = SchemaIntrospector(db_engine)
    return introspector.introspect_database(schema, table_names)


# Made with Bob