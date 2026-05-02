"""
Data Contract Models for DataContractIQ MCP Server
Defines Pydantic models for data contracts, business rules, and metadata
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ContractStatus(str, Enum):
    """Status of a data contract"""
    DRAFT = "draft"
    APPROVED = "approved"
    OUTDATED = "outdated"
    ARCHIVED = "archived"


class ChangeSeverity(str, Enum):
    """Severity level for schema changes"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ColumnContract(BaseModel):
    """Contract definition for a single column"""
    name: str = Field(..., description="Column name")
    description: str = Field(..., description="Plain English description of column purpose")
    data_type: str = Field(..., description="Data type (e.g., integer, varchar, timestamp)")
    nullable: bool = Field(..., description="Whether column allows NULL values")
    constraints: List[str] = Field(default_factory=list, description="Constraints (PRIMARY KEY, UNIQUE, etc.)")
    default_value: Optional[str] = Field(None, description="Default value if any")
    business_rules: List[str] = Field(default_factory=list, description="Business rules for this column")
    examples: List[str] = Field(default_factory=list, description="Example values")
    valid_values: Optional[List[str]] = Field(None, description="Valid values for enum-like columns")
    format: Optional[str] = Field(None, description="Format specification (e.g., email, phone, date)")
    sensitivity: Optional[str] = Field(None, description="Data sensitivity level (PII, confidential, public)")


class RelationshipContract(BaseModel):
    """Contract definition for table relationships"""
    type: str = Field(..., description="Relationship type (foreign_key, one_to_many, many_to_many)")
    column: str = Field(..., description="Source column name")
    references_table: str = Field(..., description="Referenced table name")
    references_column: str = Field(..., description="Referenced column name")
    description: str = Field(..., description="Plain English description of relationship")
    on_delete: Optional[str] = Field(None, description="ON DELETE action (CASCADE, RESTRICT, etc.)")
    on_update: Optional[str] = Field(None, description="ON UPDATE action")
    cardinality: Optional[str] = Field(None, description="Cardinality (1:1, 1:N, N:M)")


class BusinessRule(BaseModel):
    """Business rule definition"""
    rule_id: str = Field(..., description="Unique identifier for the rule")
    description: str = Field(..., description="Plain English description of the rule")
    rule_type: str = Field(..., description="Type of rule (validation, calculation, constraint)")
    enforcement: str = Field(..., description="How rule is enforced (database, application, manual)")
    sql_expression: Optional[str] = Field(None, description="SQL expression if database-enforced")
    examples: List[str] = Field(default_factory=list, description="Examples of rule application")
    exceptions: List[str] = Field(default_factory=list, description="Known exceptions to the rule")


class ContractQuestion(BaseModel):
    """Question flagged for human review"""
    question_id: str = Field(..., description="Unique identifier for the question")
    question: str = Field(..., description="The question to be answered")
    context: str = Field(..., description="Context explaining why this question is being asked")
    suggested_answers: List[str] = Field(default_factory=list, description="Suggested answer options")
    answer: Optional[str] = Field(None, description="User's answer (filled in during review)")
    answered_by: Optional[str] = Field(None, description="Who answered the question")
    answered_at: Optional[datetime] = Field(None, description="When question was answered")


class DataQualityRule(BaseModel):
    """Data quality rule definition"""
    rule_name: str = Field(..., description="Name of the quality rule")
    description: str = Field(..., description="What this rule checks")
    check_type: str = Field(..., description="Type of check (completeness, accuracy, consistency, etc.)")
    sql_query: Optional[str] = Field(None, description="SQL query to validate the rule")
    threshold: Optional[float] = Field(None, description="Acceptable threshold (e.g., 95% completeness)")
    severity: str = Field(default="warning", description="Severity if rule fails")


class ContractMetadata(BaseModel):
    """Metadata about the contract"""
    contract_id: str = Field(..., description="Unique contract identifier")
    version: str = Field(default="1.0", description="Contract version")
    status: ContractStatus = Field(default=ContractStatus.DRAFT, description="Contract status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When contract was created")
    created_by: Optional[str] = Field(None, description="Who created the contract")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    updated_by: Optional[str] = Field(None, description="Who last updated the contract")
    approved_at: Optional[datetime] = Field(None, description="When contract was approved")
    approved_by: Optional[str] = Field(None, description="Who approved the contract")
    approval_notes: Optional[str] = Field(None, description="Notes from approval process")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    confidence_score: Optional[float] = Field(None, description="AI confidence in contract accuracy (0-1)")


class DataContract(BaseModel):
    """Complete data contract for a database table"""
    
    # Basic Information
    table_name: str = Field(..., description="Name of the table")
    schema_name: str = Field(default="public", description="Database schema name")
    description: str = Field(..., description="Plain English description of table purpose")
    purpose: str = Field(..., description="Business purpose of this table")
    
    # Columns
    columns: List[ColumnContract] = Field(..., description="Column definitions")
    primary_keys: List[str] = Field(default_factory=list, description="Primary key column names")
    
    # Relationships
    relationships: List[RelationshipContract] = Field(default_factory=list, description="Table relationships")
    
    # Business Rules
    business_rules: List[BusinessRule] = Field(default_factory=list, description="Business rules for this table")
    
    # Data Quality
    data_quality_rules: List[DataQualityRule] = Field(default_factory=list, description="Data quality rules")
    
    # Questions for Review
    questions: List[ContractQuestion] = Field(default_factory=list, description="Questions needing human review")
    
    # Metadata
    metadata: ContractMetadata = Field(..., description="Contract metadata")
    
    # Additional Information
    row_count: Optional[int] = Field(None, description="Approximate number of rows")
    data_retention: Optional[str] = Field(None, description="Data retention policy")
    access_control: Optional[str] = Field(None, description="Who can access this data")
    update_frequency: Optional[str] = Field(None, description="How often data is updated")
    data_sources: List[str] = Field(default_factory=list, description="Where data comes from")
    downstream_systems: List[str] = Field(default_factory=list, description="Systems that use this data")
    notes: Optional[str] = Field(None, description="Additional notes")


class SchemaChange(BaseModel):
    """Represents a detected schema change"""
    change_type: str = Field(..., description="Type of change (column_added, column_removed, etc.)")
    table_name: str = Field(..., description="Affected table")
    column_name: Optional[str] = Field(None, description="Affected column (if applicable)")
    old_value: Optional[str] = Field(None, description="Previous value")
    new_value: Optional[str] = Field(None, description="New value")
    severity: ChangeSeverity = Field(..., description="Severity of the change")
    description: str = Field(..., description="Plain English description of the change")
    impact: str = Field(..., description="Impact assessment")
    recommendation: str = Field(..., description="Recommended action")
    breaking_change: bool = Field(default=False, description="Whether this is a breaking change")


class DriftReport(BaseModel):
    """Report of detected schema drift"""
    table_name: str = Field(..., description="Table that was checked")
    contract_id: str = Field(..., description="Contract that was compared against")
    contract_version: str = Field(..., description="Version of the contract")
    drift_detected: bool = Field(..., description="Whether drift was detected")
    changes: List[SchemaChange] = Field(default_factory=list, description="List of detected changes")
    summary: Dict[str, int] = Field(..., description="Summary counts by severity")
    checked_at: datetime = Field(default_factory=datetime.utcnow, description="When drift check was performed")
    recommendations: List[str] = Field(default_factory=list, description="Overall recommendations")


class ContractGenerationRequest(BaseModel):
    """Request to generate a data contract"""
    table_name: str = Field(..., description="Table to generate contract for")
    include_sample_data: bool = Field(default=False, description="Whether to analyze sample data")
    max_samples: int = Field(default=10, description="Number of sample rows to analyze")
    include_examples: bool = Field(default=True, description="Whether to include example values")
    format: str = Field(default="both", description="Output format (json, markdown, both)")


class ContractGenerationResponse(BaseModel):
    """Response from contract generation"""
    contract: DataContract = Field(..., description="Generated contract")
    markdown: Optional[str] = Field(None, description="Markdown representation")
    generation_time_seconds: float = Field(..., description="Time taken to generate")
    success: bool = Field(default=True, description="Whether generation succeeded")
    message: Optional[str] = Field(None, description="Success or error message")


class DriftDetectionRequest(BaseModel):
    """Request to detect schema drift"""
    table_name: str = Field(..., description="Table to check for drift")
    contract_id: Optional[str] = Field(None, description="Specific contract to compare against (uses latest if None)")


class DriftDetectionResponse(BaseModel):
    """Response from drift detection"""
    drift_report: DriftReport = Field(..., description="Detailed drift report")
    detection_time_seconds: float = Field(..., description="Time taken to detect drift")
    success: bool = Field(default=True, description="Whether detection succeeded")
    message: Optional[str] = Field(None, description="Success or error message")


# Made with Bob