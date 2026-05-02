"""
Drift Detector for DataContractIQ MCP Server
Compares current database schema against approved contracts to detect changes
"""
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime

from app.models.contract import (
    DataContract,
    SchemaChange,
    DriftReport,
    ChangeSeverity
)
from app.models.schema import DatabaseSchema, TableSchema, ColumnSchema
from app.core.schema_introspector import introspect_database
from app.core.contract_storage import get_contract_by_table

logger = logging.getLogger(__name__)


class DriftDetector:
    """Detect schema drift by comparing current schema against contracts"""
    
    def detect_drift(
        self,
        table_name: str,
        contract: Optional[DataContract] = None,
        current_schema: Optional[TableSchema] = None
    ) -> DriftReport:
        """
        Detect drift for a specific table.
        
        Args:
            table_name: Table to check for drift
            contract: Contract to compare against (loads latest if None)
            current_schema: Current table schema (introspects if None)
            
        Returns:
            DriftReport: Detailed drift analysis
        """
        logger.info(f"Detecting drift for table: {table_name}")
        
        # Load contract if not provided
        if contract is None:
            contract = get_contract_by_table(table_name)
            if contract is None:
                raise ValueError(f"No approved contract found for table: {table_name}")
        
        # Get current schema if not provided
        if current_schema is None:
            db_schema = introspect_database(schema="public", table_names=[table_name])
            if not db_schema.tables:
                raise ValueError(f"Table not found in database: {table_name}")
            current_schema = db_schema.tables[0]
        
        # Detect changes
        changes = []
        
        # Check for column changes
        changes.extend(self._detect_column_changes(contract, current_schema))
        
        # Check for constraint changes
        changes.extend(self._detect_constraint_changes(contract, current_schema))
        
        # Check for relationship changes
        changes.extend(self._detect_relationship_changes(contract, current_schema))
        
        # Generate summary
        summary = self._generate_summary(changes)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(changes)
        
        drift_report = DriftReport(
            table_name=table_name,
            contract_id=contract.metadata.contract_id,
            contract_version=contract.metadata.version,
            drift_detected=len(changes) > 0,
            changes=changes,
            summary=summary,
            recommendations=recommendations
        )
        
        logger.info(f"Drift detection complete: {len(changes)} changes found")
        return drift_report
    
    def _detect_column_changes(
        self,
        contract: DataContract,
        current_schema: TableSchema
    ) -> List[SchemaChange]:
        """Detect changes in columns"""
        changes = []
        
        # Build maps for easy lookup
        contract_columns = {col.name: col for col in contract.columns}
        current_columns = {col.name: col for col in current_schema.columns}
        
        # Check for added columns
        for col_name in current_columns:
            if col_name not in contract_columns:
                current_col = current_columns[col_name]
                changes.append(SchemaChange(
                    change_type="column_added",
                    table_name=contract.table_name,
                    column_name=col_name,
                    old_value=None,
                    new_value=f"{current_col.data_type}",
                    severity=ChangeSeverity.WARNING,
                    description=f"New column '{col_name}' added with type {current_col.data_type}",
                    impact="Contract needs update. Existing queries unaffected unless they use SELECT *.",
                    recommendation=f"Update contract to document the new '{col_name}' column.",
                    breaking_change=False
                ))
        
        # Check for removed columns
        for col_name in contract_columns:
            if col_name not in current_columns:
                contract_col = contract_columns[col_name]
                changes.append(SchemaChange(
                    change_type="column_removed",
                    table_name=contract.table_name,
                    column_name=col_name,
                    old_value=f"{contract_col.data_type}",
                    new_value=None,
                    severity=ChangeSeverity.CRITICAL,
                    description=f"Column '{col_name}' has been removed",
                    impact="BREAKING: Queries referencing this column will fail.",
                    recommendation=f"Update all queries and applications that reference '{col_name}'.",
                    breaking_change=True
                ))
        
        # Check for modified columns
        for col_name in contract_columns:
            if col_name in current_columns:
                contract_col = contract_columns[col_name]
                current_col = current_columns[col_name]
                
                # Check data type change
                if contract_col.data_type.lower() != current_col.data_type.lower():
                    severity = self._assess_type_change_severity(
                        contract_col.data_type,
                        current_col.data_type
                    )
                    changes.append(SchemaChange(
                        change_type="column_type_changed",
                        table_name=contract.table_name,
                        column_name=col_name,
                        old_value=contract_col.data_type,
                        new_value=current_col.data_type,
                        severity=severity,
                        description=f"Column '{col_name}' type changed from {contract_col.data_type} to {current_col.data_type}",
                        impact="May cause data loss or query failures depending on type compatibility.",
                        recommendation=f"Verify data compatibility and update contract for '{col_name}'.",
                        breaking_change=(severity == ChangeSeverity.CRITICAL)
                    ))
                
                # Check nullability change
                if contract_col.nullable != current_col.nullable:
                    if current_col.nullable and not contract_col.nullable:
                        # Now allows NULL (less restrictive)
                        severity = ChangeSeverity.INFO
                        impact = "Column now allows NULL values. Existing data unaffected."
                        breaking = False
                    else:
                        # Now requires NOT NULL (more restrictive)
                        severity = ChangeSeverity.CRITICAL
                        impact = "BREAKING: Column now requires NOT NULL. Existing NULL values will cause errors."
                        breaking = True
                    
                    changes.append(SchemaChange(
                        change_type="column_nullability_changed",
                        table_name=contract.table_name,
                        column_name=col_name,
                        old_value="NULL" if contract_col.nullable else "NOT NULL",
                        new_value="NULL" if current_col.nullable else "NOT NULL",
                        severity=severity,
                        description=f"Column '{col_name}' nullability changed",
                        impact=impact,
                        recommendation=f"Update contract and verify data integrity for '{col_name}'.",
                        breaking_change=breaking
                    ))
                
                # Check default value change
                if contract_col.default_value != current_col.default_value:
                    changes.append(SchemaChange(
                        change_type="column_default_changed",
                        table_name=contract.table_name,
                        column_name=col_name,
                        old_value=str(contract_col.default_value) if contract_col.default_value else "None",
                        new_value=str(current_col.default_value) if current_col.default_value else "None",
                        severity=ChangeSeverity.WARNING,
                        description=f"Column '{col_name}' default value changed",
                        impact="New inserts will use different default value.",
                        recommendation=f"Update contract and verify business logic for '{col_name}'.",
                        breaking_change=False
                    ))
        
        return changes
    
    def _detect_constraint_changes(
        self,
        contract: DataContract,
        current_schema: TableSchema
    ) -> List[SchemaChange]:
        """Detect changes in constraints"""
        changes = []
        
        # Check primary key changes
        contract_pks = set(contract.primary_keys)
        current_pks = set(current_schema.primary_keys)
        
        if contract_pks != current_pks:
            added_pks = current_pks - contract_pks
            removed_pks = contract_pks - current_pks
            
            if added_pks:
                changes.append(SchemaChange(
                    change_type="primary_key_added",
                    table_name=contract.table_name,
                    column_name=", ".join(added_pks),
                    old_value=None,
                    new_value=", ".join(current_pks),
                    severity=ChangeSeverity.CRITICAL,
                    description=f"Primary key columns added: {', '.join(added_pks)}",
                    impact="BREAKING: Changes table's unique identifier structure.",
                    recommendation="Update contract and verify all foreign key relationships.",
                    breaking_change=True
                ))
            
            if removed_pks:
                changes.append(SchemaChange(
                    change_type="primary_key_removed",
                    table_name=contract.table_name,
                    column_name=", ".join(removed_pks),
                    old_value=", ".join(contract_pks),
                    new_value=None,
                    severity=ChangeSeverity.CRITICAL,
                    description=f"Primary key columns removed: {', '.join(removed_pks)}",
                    impact="BREAKING: Changes table's unique identifier structure.",
                    recommendation="Update contract and verify all foreign key relationships.",
                    breaking_change=True
                ))
        
        return changes
    
    def _detect_relationship_changes(
        self,
        contract: DataContract,
        current_schema: TableSchema
    ) -> List[SchemaChange]:
        """Detect changes in foreign key relationships"""
        changes = []
        
        # Build maps for comparison
        contract_fks = {
            (fk.column, fk.references_table, fk.references_column): fk
            for fk in contract.relationships
        }
        
        current_fks = {
            (fk.column_name, fk.referenced_table, fk.referenced_column): fk
            for fk in current_schema.foreign_keys
        }
        
        # Check for added foreign keys
        for fk_key in current_fks:
            if fk_key not in contract_fks:
                fk = current_fks[fk_key]
                changes.append(SchemaChange(
                    change_type="foreign_key_added",
                    table_name=contract.table_name,
                    column_name=fk.column_name,
                    old_value=None,
                    new_value=f"{fk.referenced_table}.{fk.referenced_column}",
                    severity=ChangeSeverity.WARNING,
                    description=f"New foreign key: {fk.column_name} → {fk.referenced_table}.{fk.referenced_column}",
                    impact="Adds referential integrity constraint. May affect data insertion.",
                    recommendation="Update contract to document the new relationship.",
                    breaking_change=False
                ))
        
        # Check for removed foreign keys
        for fk_key in contract_fks:
            if fk_key not in current_fks:
                fk = contract_fks[fk_key]
                changes.append(SchemaChange(
                    change_type="foreign_key_removed",
                    table_name=contract.table_name,
                    column_name=fk.column,
                    old_value=f"{fk.references_table}.{fk.references_column}",
                    new_value=None,
                    severity=ChangeSeverity.CRITICAL,
                    description=f"Foreign key removed: {fk.column} → {fk.references_table}.{fk.references_column}",
                    impact="BREAKING: Removes referential integrity. Data consistency at risk.",
                    recommendation="Update contract and verify data integrity manually.",
                    breaking_change=True
                ))
        
        return changes
    
    def _assess_type_change_severity(self, old_type: str, new_type: str) -> ChangeSeverity:
        """Assess severity of a data type change"""
        old_type = old_type.lower()
        new_type = new_type.lower()
        
        # Compatible widening changes (less severe)
        compatible_widenings = [
            ("integer", "bigint"),
            ("smallint", "integer"),
            ("smallint", "bigint"),
            ("numeric", "double precision"),
            ("varchar", "text"),
        ]
        
        for old, new in compatible_widenings:
            if old in old_type and new in new_type:
                return ChangeSeverity.INFO
        
        # Potentially compatible changes (warning)
        if ("int" in old_type and "int" in new_type) or \
           ("char" in old_type and "char" in new_type):
            return ChangeSeverity.WARNING
        
        # Incompatible changes (critical)
        return ChangeSeverity.CRITICAL
    
    def _generate_summary(self, changes: List[SchemaChange]) -> Dict[str, int]:
        """Generate summary counts by severity"""
        summary = {
            "critical": 0,
            "warning": 0,
            "info": 0
        }
        
        for change in changes:
            summary[change.severity.value] += 1
        
        return summary
    
    def _generate_recommendations(self, changes: List[SchemaChange]) -> List[str]:
        """Generate overall recommendations based on detected changes"""
        recommendations = []
        
        if not changes:
            recommendations.append("✅ No drift detected. Schema matches contract.")
            return recommendations
        
        # Count by severity
        critical_count = sum(1 for c in changes if c.severity == ChangeSeverity.CRITICAL)
        warning_count = sum(1 for c in changes if c.severity == ChangeSeverity.WARNING)
        breaking_count = sum(1 for c in changes if c.breaking_change)
        
        if critical_count > 0:
            recommendations.append(
                f"🚨 CRITICAL: {critical_count} critical change(s) detected. "
                "Immediate action required."
            )
        
        if breaking_count > 0:
            recommendations.append(
                f"⚠️ {breaking_count} breaking change(s) detected. "
                "Update all dependent systems before deploying."
            )
        
        if warning_count > 0:
            recommendations.append(
                f"⚠️ {warning_count} warning(s) detected. "
                "Review and update contract documentation."
            )
        
        # Specific recommendations
        if any(c.change_type == "column_removed" for c in changes):
            recommendations.append(
                "📝 Update all queries and applications that reference removed columns."
            )
        
        if any(c.change_type == "column_type_changed" for c in changes):
            recommendations.append(
                "🔍 Verify data compatibility for type changes. Consider data migration."
            )
        
        if any(c.change_type.startswith("foreign_key") for c in changes):
            recommendations.append(
                "🔗 Review and update relationship documentation in contract."
            )
        
        recommendations.append(
            "📄 Update the data contract to reflect current schema state."
        )
        
        return recommendations
    
    def compare_schemas(
        self,
        schema1: DatabaseSchema,
        schema2: DatabaseSchema,
        table_name: Optional[str] = None
    ) -> List[DriftReport]:
        """
        Compare two complete database schemas.
        
        Args:
            schema1: First schema (baseline)
            schema2: Second schema (current)
            table_name: Specific table to compare (None = all tables)
            
        Returns:
            List[DriftReport]: Drift reports for each table
        """
        reports = []
        
        # Build table maps
        tables1 = {t.table_name: t for t in schema1.tables}
        tables2 = {t.table_name: t for t in schema2.tables}
        
        # Filter by table name if specified
        if table_name:
            if table_name not in tables1 or table_name not in tables2:
                raise ValueError(f"Table '{table_name}' not found in one or both schemas")
            tables_to_compare = [table_name]
        else:
            tables_to_compare = set(tables1.keys()) | set(tables2.keys())
        
        for tname in tables_to_compare:
            # Handle table additions/removals
            if tname not in tables1:
                # Table added
                logger.info(f"Table '{tname}' added in schema2")
                continue
            
            if tname not in tables2:
                # Table removed
                logger.info(f"Table '{tname}' removed in schema2")
                continue
            
            # Compare existing tables
            # Note: This would need a contract for proper drift detection
            # For now, we'll skip tables without contracts
            logger.debug(f"Comparing table: {tname}")
        
        return reports


# Global drift detector instance
drift_detector = DriftDetector()


def detect_drift(
    table_name: str,
    contract: Optional[DataContract] = None,
    current_schema: Optional[TableSchema] = None
) -> DriftReport:
    """
    Convenience function to detect drift using the global detector.
    
    Args:
        table_name: Table to check for drift
        contract: Contract to compare against (loads latest if None)
        current_schema: Current table schema (introspects if None)
        
    Returns:
        DriftReport: Detailed drift analysis
    """
    return drift_detector.detect_drift(table_name, contract, current_schema)


# Made with Bob