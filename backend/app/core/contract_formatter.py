"""
Contract Formatter for DataContractIQ MCP Server
Converts data contracts between JSON and Markdown formats
"""
from typing import List, Optional
import logging

from app.models.contract import (
    DataContract,
    ColumnContract,
    RelationshipContract,
    BusinessRule,
    ContractQuestion,
    DataQualityRule
)

logger = logging.getLogger(__name__)


class ContractFormatter:
    """Format data contracts as human-readable Markdown"""
    
    def contract_to_markdown(self, contract: DataContract) -> str:
        """
        Convert a DataContract to Markdown format.
        
        Args:
            contract: Contract to convert
            
        Returns:
            str: Markdown representation
        """
        sections = []
        
        # Header
        sections.append(self._format_header(contract))
        
        # Table of Contents
        sections.append(self._format_toc())
        
        # Overview
        sections.append(self._format_overview(contract))
        
        # Columns
        sections.append(self._format_columns(contract.columns, contract.primary_keys))
        
        # Relationships
        if contract.relationships:
            sections.append(self._format_relationships(contract.relationships))
        
        # Business Rules
        if contract.business_rules:
            sections.append(self._format_business_rules(contract.business_rules))
        
        # Data Quality Rules
        if contract.data_quality_rules:
            sections.append(self._format_data_quality_rules(contract.data_quality_rules))
        
        # Questions for Review
        if contract.questions:
            sections.append(self._format_questions(contract.questions))
        
        # Additional Information
        sections.append(self._format_additional_info(contract))
        
        # Metadata
        sections.append(self._format_metadata(contract))
        
        return "\n\n".join(sections)
    
    def _format_header(self, contract: DataContract) -> str:
        """Format the document header"""
        status_emoji = {
            "draft": "📝",
            "approved": "✅",
            "outdated": "⚠️",
            "archived": "📦"
        }
        
        emoji = status_emoji.get(contract.metadata.status.value, "📄")
        
        return f"""# {emoji} Data Contract: `{contract.table_name}`

**Schema:** `{contract.schema_name}`  
**Status:** {contract.metadata.status.value.upper()}  
**Version:** {contract.metadata.version}  
**Last Updated:** {contract.metadata.updated_at.strftime('%Y-%m-%d %H:%M:%S') if contract.metadata.updated_at else 'N/A'}

---"""
    
    def _format_toc(self) -> str:
        """Format table of contents"""
        return """## 📑 Table of Contents

1. [Overview](#overview)
2. [Columns](#columns)
3. [Relationships](#relationships)
4. [Business Rules](#business-rules)
5. [Data Quality Rules](#data-quality-rules)
6. [Questions for Review](#questions-for-review)
7. [Additional Information](#additional-information)
8. [Metadata](#metadata)

---"""
    
    def _format_overview(self, contract: DataContract) -> str:
        """Format overview section"""
        lines = [
            "## 📋 Overview",
            "",
            f"**Purpose:** {contract.purpose}",
            "",
            f"**Description:** {contract.description}",
            ""
        ]
        
        if contract.row_count:
            lines.append(f"**Approximate Row Count:** {contract.row_count:,}")
            lines.append("")
        
        if contract.data_sources:
            lines.append(f"**Data Sources:** {', '.join(contract.data_sources)}")
            lines.append("")
        
        if contract.downstream_systems:
            lines.append(f"**Downstream Systems:** {', '.join(contract.downstream_systems)}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_columns(self, columns: List[ColumnContract], primary_keys: List[str]) -> str:
        """Format columns section"""
        lines = [
            "## 📊 Columns",
            "",
            f"**Total Columns:** {len(columns)}",
            ""
        ]
        
        for col in columns:
            # Column header with emoji
            emoji = "🔑" if col.name in primary_keys else "📌"
            lines.append(f"### {emoji} `{col.name}`")
            lines.append("")
            
            # Description
            lines.append(f"**Description:** {col.description}")
            lines.append("")
            
            # Technical details
            lines.append("**Technical Details:**")
            lines.append(f"- **Type:** `{col.data_type}`")
            lines.append(f"- **Nullable:** {'Yes' if col.nullable else 'No'}")
            
            if col.default_value:
                lines.append(f"- **Default:** `{col.default_value}`")
            
            if col.constraints:
                lines.append(f"- **Constraints:** {', '.join(col.constraints)}")
            
            if col.format:
                lines.append(f"- **Format:** {col.format}")
            
            if col.sensitivity:
                lines.append(f"- **Sensitivity:** {col.sensitivity}")
            
            lines.append("")
            
            # Business rules
            if col.business_rules:
                lines.append("**Business Rules:**")
                for rule in col.business_rules:
                    lines.append(f"- {rule}")
                lines.append("")
            
            # Valid values
            if col.valid_values:
                lines.append("**Valid Values:**")
                for value in col.valid_values:
                    lines.append(f"- `{value}`")
                lines.append("")
            
            # Examples
            if col.examples:
                lines.append("**Examples:**")
                for example in col.examples:
                    lines.append(f"- `{example}`")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_relationships(self, relationships: List[RelationshipContract]) -> str:
        """Format relationships section"""
        lines = [
            "## 🔗 Relationships",
            "",
            f"**Total Relationships:** {len(relationships)}",
            ""
        ]
        
        for rel in relationships:
            lines.append(f"### {rel.type.upper()}: `{rel.column}` → `{rel.references_table}.{rel.references_column}`")
            lines.append("")
            lines.append(f"**Description:** {rel.description}")
            lines.append("")
            
            if rel.cardinality:
                lines.append(f"**Cardinality:** {rel.cardinality}")
            
            if rel.on_delete:
                lines.append(f"**On Delete:** {rel.on_delete}")
            
            if rel.on_update:
                lines.append(f"**On Update:** {rel.on_update}")
            
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_business_rules(self, rules: List[BusinessRule]) -> str:
        """Format business rules section"""
        lines = [
            "## 📜 Business Rules",
            "",
            f"**Total Rules:** {len(rules)}",
            ""
        ]
        
        for i, rule in enumerate(rules, 1):
            lines.append(f"### Rule {i}: {rule.rule_id}")
            lines.append("")
            lines.append(f"**Description:** {rule.description}")
            lines.append("")
            lines.append(f"**Type:** {rule.rule_type}")
            lines.append(f"**Enforcement:** {rule.enforcement}")
            lines.append("")
            
            if rule.sql_expression:
                lines.append("**SQL Expression:**")
                lines.append("```sql")
                lines.append(rule.sql_expression)
                lines.append("```")
                lines.append("")
            
            if rule.examples:
                lines.append("**Examples:**")
                for example in rule.examples:
                    lines.append(f"- {example}")
                lines.append("")
            
            if rule.exceptions:
                lines.append("**Exceptions:**")
                for exception in rule.exceptions:
                    lines.append(f"- {exception}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_data_quality_rules(self, rules: List[DataQualityRule]) -> str:
        """Format data quality rules section"""
        lines = [
            "## ✅ Data Quality Rules",
            "",
            f"**Total Quality Rules:** {len(rules)}",
            ""
        ]
        
        for rule in rules:
            lines.append(f"### {rule.rule_name}")
            lines.append("")
            lines.append(f"**Description:** {rule.description}")
            lines.append(f"**Check Type:** {rule.check_type}")
            lines.append(f"**Severity:** {rule.severity}")
            
            if rule.threshold:
                lines.append(f"**Threshold:** {rule.threshold * 100}%")
            
            lines.append("")
            
            if rule.sql_query:
                lines.append("**Validation Query:**")
                lines.append("```sql")
                lines.append(rule.sql_query)
                lines.append("```")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_questions(self, questions: List[ContractQuestion]) -> str:
        """Format questions section"""
        lines = [
            "## ❓ Questions for Review",
            "",
            f"**Total Questions:** {len(questions)}",
            ""
        ]
        
        for i, q in enumerate(questions, 1):
            status = "✅ Answered" if q.answer else "⏳ Pending"
            lines.append(f"### Question {i}: {status}")
            lines.append("")
            lines.append(f"**Question:** {q.question}")
            lines.append("")
            lines.append(f"**Context:** {q.context}")
            lines.append("")
            
            if q.suggested_answers:
                lines.append("**Suggested Answers:**")
                for answer in q.suggested_answers:
                    lines.append(f"- {answer}")
                lines.append("")
            
            if q.answer:
                lines.append(f"**Answer:** {q.answer}")
                if q.answered_by:
                    lines.append(f"**Answered By:** {q.answered_by}")
                if q.answered_at:
                    lines.append(f"**Answered At:** {q.answered_at.strftime('%Y-%m-%d %H:%M:%S')}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_additional_info(self, contract: DataContract) -> str:
        """Format additional information section"""
        lines = [
            "## ℹ️ Additional Information",
            ""
        ]
        
        if contract.data_retention:
            lines.append(f"**Data Retention:** {contract.data_retention}")
        
        if contract.access_control:
            lines.append(f"**Access Control:** {contract.access_control}")
        
        if contract.update_frequency:
            lines.append(f"**Update Frequency:** {contract.update_frequency}")
        
        if contract.notes:
            lines.append("")
            lines.append("**Notes:**")
            lines.append("")
            lines.append(contract.notes)
        
        lines.append("")
        return "\n".join(lines)
    
    def _format_metadata(self, contract: DataContract) -> str:
        """Format metadata section"""
        meta = contract.metadata
        
        lines = [
            "## 📝 Metadata",
            "",
            f"**Contract ID:** `{meta.contract_id}`",
            f"**Version:** {meta.version}",
            f"**Status:** {meta.status.value}",
            f"**Created:** {meta.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        
        if meta.created_by:
            lines.append(f"**Created By:** {meta.created_by}")
        
        if meta.updated_at:
            lines.append(f"**Updated:** {meta.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if meta.updated_by:
            lines.append(f"**Updated By:** {meta.updated_by}")
        
        if meta.approved_at:
            lines.append(f"**Approved:** {meta.approved_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if meta.approved_by:
            lines.append(f"**Approved By:** {meta.approved_by}")
        
        if meta.approval_notes:
            lines.append(f"**Approval Notes:** {meta.approval_notes}")
        
        if meta.tags:
            lines.append(f"**Tags:** {', '.join(meta.tags)}")
        
        if meta.confidence_score:
            lines.append(f"**AI Confidence Score:** {meta.confidence_score * 100:.1f}%")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("*Generated by DataContractIQ MCP Server*")
        
        return "\n".join(lines)


# Global formatter instance
contract_formatter = ContractFormatter()


def contract_to_markdown(contract: DataContract) -> str:
    """
    Convenience function to convert contract to Markdown.
    
    Args:
        contract: Contract to convert
        
    Returns:
        str: Markdown representation
    """
    return contract_formatter.contract_to_markdown(contract)


# Made with Bob