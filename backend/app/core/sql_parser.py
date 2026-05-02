"""
SQL DDL Parser for extracting schema metadata from .sql files
Parses CREATE TABLE, CREATE TYPE, and constraint definitions
"""
import re
from typing import List, Dict, Optional, Tuple
import logging

from app.models.schema import (
    TableSchema,
    ColumnSchema,
    ForeignKeyConstraint,
    CheckConstraint,
    CustomType,
    DatabaseSchema
)

logger = logging.getLogger(__name__)


class SQLParser:
    """Parser for PostgreSQL DDL statements"""
    
    def __init__(self):
        self.tables: Dict[str, TableSchema] = {}
        self.custom_types: List[CustomType] = []
        self.primary_keys: Dict[str, List[str]] = {}
        self.foreign_keys: Dict[str, List[ForeignKeyConstraint]] = {}
        
    def parse_sql_file(self, file_path: str) -> DatabaseSchema:
        """
        Parse a SQL file and extract complete database schema.
        
        Args:
            file_path: Path to .sql file
            
        Returns:
            DatabaseSchema: Complete database schema metadata
        """
        logger.info(f"Parsing SQL file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Parse in order: types, tables, constraints
        self._parse_custom_types(sql_content)
        self._parse_create_tables(sql_content)
        self._parse_primary_keys(sql_content)
        self._parse_foreign_keys(sql_content)
        
        # Apply constraints to tables
        self._apply_constraints_to_tables()
        
        # Extract database name from file path
        db_name = self._extract_database_name(file_path)
        
        database_schema = DatabaseSchema(
            database_name=db_name,
            tables=list(self.tables.values()),
            custom_types=self.custom_types,
            total_tables=len(self.tables),
            database_version=None
        )
        
        logger.info(f"Parsed {len(self.tables)} tables and {len(self.custom_types)} custom types")
        return database_schema
    
    def _parse_custom_types(self, sql_content: str) -> None:
        """Parse CREATE TYPE statements (ENUMs and DOMAINs)"""
        
        # Parse ENUM types
        enum_pattern = r"CREATE TYPE\s+(\w+\.)?(\w+)\s+AS\s+ENUM\s*\((.*?)\);"
        for match in re.finditer(enum_pattern, sql_content, re.DOTALL | re.IGNORECASE):
            schema_name = match.group(1).rstrip('.') if match.group(1) else 'public'
            type_name = match.group(2)
            values_str = match.group(3)
            
            # Extract enum values
            values = [v.strip().strip("'") for v in values_str.split(',')]
            
            custom_type = CustomType(
                type_name=type_name,
                type_category="enum",
                values=values,
                base_type=None,
                constraints=None
            )
            self.custom_types.append(custom_type)
            logger.debug(f"Found ENUM type: {type_name} with {len(values)} values")
        
        # Parse DOMAIN types
        domain_pattern = r"CREATE DOMAIN\s+(\w+\.)?(\w+)\s+AS\s+(\w+)(.*?);"
        for match in re.finditer(domain_pattern, sql_content, re.DOTALL | re.IGNORECASE):
            schema_name = match.group(1).rstrip('.') if match.group(1) else 'public'
            type_name = match.group(2)
            base_type = match.group(3)
            constraints_str = match.group(4)
            
            # Extract constraints
            constraints = []
            if 'CONSTRAINT' in constraints_str.upper():
                constraint_matches = re.findall(r'CONSTRAINT\s+\w+\s+CHECK\s*\((.*?)\)', constraints_str, re.IGNORECASE)
                constraints.extend(constraint_matches)
            
            custom_type = CustomType(
                type_name=type_name,
                type_category="domain",
                base_type=base_type,
                constraints=constraints if constraints else None,
                values=None
            )
            self.custom_types.append(custom_type)
            logger.debug(f"Found DOMAIN type: {type_name} based on {base_type}")
    
    def _parse_create_tables(self, sql_content: str) -> None:
        """Parse CREATE TABLE statements"""
        
        # Pattern to match CREATE TABLE with all columns
        table_pattern = r"CREATE TABLE\s+(\w+\.)?(\w+)\s*\((.*?)\);"
        
        for match in re.finditer(table_pattern, sql_content, re.DOTALL | re.IGNORECASE):
            schema_name = match.group(1).rstrip('.') if match.group(1) else 'public'
            table_name = match.group(2)
            columns_str = match.group(3)
            
            columns = self._parse_columns(columns_str)
            
            table_schema = TableSchema(
                table_name=table_name,
                schema_name=schema_name,
                columns=columns,
                primary_keys=[],
                foreign_keys=[],
                check_constraints=[],
                unique_constraints=[],
                indexes=[],
                table_comment=None,
                row_count=None
            )
            
            self.tables[table_name] = table_schema
            logger.debug(f"Found table: {table_name} with {len(columns)} columns")
    
    def _parse_columns(self, columns_str: str) -> List[ColumnSchema]:
        """Parse column definitions from CREATE TABLE statement"""
        columns = []
        
        # Split by comma, but be careful with function calls like nextval()
        column_lines = self._split_column_definitions(columns_str)
        
        for line in column_lines:
            line = line.strip()
            if not line or line.upper().startswith('CONSTRAINT'):
                continue
            
            column = self._parse_single_column(line)
            if column:
                columns.append(column)
        
        return columns
    
    def _split_column_definitions(self, columns_str: str) -> List[str]:
        """Split column definitions, handling nested parentheses"""
        result = []
        current = []
        paren_depth = 0
        
        for char in columns_str:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif char == ',' and paren_depth == 0:
                result.append(''.join(current))
                current = []
                continue
            current.append(char)
        
        if current:
            result.append(''.join(current))
        
        return result
    
    def _parse_single_column(self, column_def: str) -> Optional[ColumnSchema]:
        """Parse a single column definition"""
        
        # Extract column name (first word)
        parts = column_def.split()
        if len(parts) < 2:
            return None
        
        column_name = parts[0]
        remaining = ' '.join(parts[1:])
        
        # Extract data type (handle types with parameters like numeric(4,2))
        data_type_match = re.match(r'(\w+(?:\[\])?(?:\s+with\s+time\s+zone)?|\w+\.\w+)(?:\(([^)]+)\))?', remaining, re.IGNORECASE)
        if not data_type_match:
            return None
        
        data_type = data_type_match.group(1)
        type_params = data_type_match.group(2)
        
        # Parse type parameters for precision/scale/length
        max_length = None
        precision = None
        scale = None
        
        if type_params:
            params = [p.strip() for p in type_params.split(',')]
            if len(params) == 1:
                max_length = int(params[0]) if params[0].isdigit() else None
                precision = max_length
            elif len(params) == 2:
                precision = int(params[0]) if params[0].isdigit() else None
                scale = int(params[1]) if params[1].isdigit() else None
        
        # Check for constraints
        nullable = 'NOT NULL' not in remaining.upper()
        unique = 'UNIQUE' in remaining.upper()
        
        # Extract default value
        default_value = None
        default_match = re.search(r'DEFAULT\s+(.+?)(?:\s+NOT\s+NULL|\s+UNIQUE|$)', remaining, re.IGNORECASE)
        if default_match:
            default_value = default_match.group(1).strip()
        
        # Check for auto-increment (nextval)
        auto_increment = 'nextval' in remaining.lower()
        
        column_schema = ColumnSchema(
            name=column_name,
            data_type=data_type,
            nullable=nullable,
            default_value=default_value,
            primary_key=False,  # Will be set later
            foreign_key=None,   # Will be set later
            unique=unique,
            auto_increment=auto_increment,
            max_length=max_length,
            precision=precision,
            scale=scale,
            description=None
        )
        
        return column_schema
    
    def _parse_primary_keys(self, sql_content: str) -> None:
        """Parse PRIMARY KEY constraints from ALTER TABLE statements"""
        
        pk_pattern = r"ALTER TABLE\s+(?:ONLY\s+)?(\w+\.)?(\w+)\s+ADD CONSTRAINT\s+\w+\s+PRIMARY KEY\s*\(([^)]+)\);"
        
        for match in re.finditer(pk_pattern, sql_content, re.IGNORECASE):
            table_name = match.group(2)
            pk_columns_str = match.group(3)
            
            # Split column names
            pk_columns = [col.strip() for col in pk_columns_str.split(',')]
            
            self.primary_keys[table_name] = pk_columns
            logger.debug(f"Found PRIMARY KEY for {table_name}: {pk_columns}")
    
    def _parse_foreign_keys(self, sql_content: str) -> None:
        """Parse FOREIGN KEY constraints from ALTER TABLE statements"""
        
        fk_pattern = r"ALTER TABLE\s+(?:ONLY\s+)?(\w+\.)?(\w+)\s+ADD CONSTRAINT\s+\w+\s+FOREIGN KEY\s*\(([^)]+)\)\s+REFERENCES\s+(\w+\.)?(\w+)\(([^)]+)\)(?:\s+ON UPDATE\s+(\w+))?(?:\s+ON DELETE\s+(\w+))?;"
        
        for match in re.finditer(fk_pattern, sql_content, re.IGNORECASE):
            source_table = match.group(2)
            source_column = match.group(3).strip()
            ref_table = match.group(5)
            ref_column = match.group(6).strip()
            on_update = match.group(7)
            on_delete = match.group(8)
            
            fk_constraint = ForeignKeyConstraint(
                column_name=source_column,
                referenced_table=ref_table,
                referenced_column=ref_column,
                on_delete=on_delete,
                on_update=on_update
            )
            
            if source_table not in self.foreign_keys:
                self.foreign_keys[source_table] = []
            
            self.foreign_keys[source_table].append(fk_constraint)
            logger.debug(f"Found FOREIGN KEY: {source_table}.{source_column} -> {ref_table}.{ref_column}")
    
    def _apply_constraints_to_tables(self) -> None:
        """Apply parsed constraints to table schemas"""
        
        for table_name, table_schema in self.tables.items():
            # Apply primary keys
            if table_name in self.primary_keys:
                pk_columns = self.primary_keys[table_name]
                table_schema.primary_keys = pk_columns
                
                # Mark columns as primary key
                for column in table_schema.columns:
                    if column.name in pk_columns:
                        column.primary_key = True
            
            # Apply foreign keys
            if table_name in self.foreign_keys:
                table_schema.foreign_keys = self.foreign_keys[table_name]
                
                # Mark columns with foreign key reference
                for fk in self.foreign_keys[table_name]:
                    for column in table_schema.columns:
                        if column.name == fk.column_name:
                            column.foreign_key = f"{fk.referenced_table}.{fk.referenced_column}"
    
    def _extract_database_name(self, file_path: str) -> str:
        """Extract database name from file path"""
        # Try to get from filename
        import os
        filename = os.path.basename(file_path)
        
        # Remove extension and common suffixes
        db_name = filename.replace('.sql', '').replace('-insert-data', '').replace('_', ' ')
        
        return db_name.title() if db_name else "Unknown Database"


def parse_sql_file(file_path: str) -> DatabaseSchema:
    """
    Convenience function to parse a SQL file.
    
    Args:
        file_path: Path to .sql file
        
    Returns:
        DatabaseSchema: Complete database schema metadata
    """
    parser = SQLParser()
    return parser.parse_sql_file(file_path)


# Made with Bob