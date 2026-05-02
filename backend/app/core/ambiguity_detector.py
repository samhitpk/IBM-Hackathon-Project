"""
Ambiguity Detection Module for DataContractIQ
Analyzes database schemas to identify areas needing human clarification
"""
import uuid
from typing import List, Set
from datetime import datetime

from app.models.schema import TableSchema, ColumnSchema, ForeignKeyConstraint
from app.models.contract import ContractQuestion


# Generic column names that likely need clarification
GENERIC_COLUMN_NAMES = {
    'data', 'value', 'info', 'information', 'details', 'content',
    'text', 'field', 'attribute', 'property', 'metadata', 'extra',
    'misc', 'other', 'additional', 'custom', 'temp', 'tmp'
}

# Column names that might contain sensitive data
POTENTIAL_PII_KEYWORDS = {
    'email', 'phone', 'address', 'ssn', 'social', 'credit', 'card',
    'password', 'secret', 'token', 'key', 'birth', 'dob', 'salary',
    'income', 'medical', 'health', 'diagnosis', 'prescription'
}

# Data types that commonly need validation rules
VALIDATION_PRONE_TYPES = {
    'varchar', 'text', 'char', 'string', 'numeric', 'decimal',
    'integer', 'int', 'smallint', 'bigint', 'real', 'double'
}


def detect_column_ambiguities(column: ColumnSchema, table_name: str) -> List[ContractQuestion]:
    """
    Detect ambiguities in a column definition.
    
    Args:
        column: Column schema to analyze
        table_name: Name of the table (for context)
        
    Returns:
        List of questions needing human clarification
    """
    questions = []
    
    # Check for generic column names
    if column.name.lower() in GENERIC_COLUMN_NAMES:
        questions.append(ContractQuestion(
            question_id=_generate_question_id(),
            question=f"What does the '{column.name}' column represent in business terms?",
            context=f"The column '{column.name}' in table '{table_name}' has a generic name that doesn't clearly indicate its purpose. Please provide a clear business description.",
            suggested_answers=[
                "Provide a specific business description",
                "Rename column to be more descriptive"
            ],
            answer=None,
            answered_by=None,
            answered_at=None
        ))
    
    # Check for nullable columns without clear reason
    if column.nullable and not column.foreign_key and column.name.lower() not in ['description', 'notes', 'comments']:
        questions.append(ContractQuestion(
            question_id=_generate_question_id(),
            question=f"What does NULL mean for the '{column.name}' column?",
            context=f"The column '{column.name}' allows NULL values. Please clarify what NULL represents in business terms (e.g., 'not applicable', 'unknown', 'optional').",
            suggested_answers=[
                "NULL means 'not applicable'",
                "NULL means 'unknown' or 'not yet provided'",
                "NULL means 'optional field'",
                "NULL should not be allowed - add NOT NULL constraint"
            ],
            answer=None,
            answered_by=None,
            answered_at=None
        ))
    
    # Check for columns that might need validation rules
    if _needs_validation_rule(column):
        questions.append(ContractQuestion(
            question_id=_generate_question_id(),
            question=f"What validation rules should apply to '{column.name}'?",
            context=f"The column '{column.name}' (type: {column.data_type}) may need validation rules. Please specify any constraints, formats, or acceptable value ranges.",
            suggested_answers=[
                "Specify min/max values or length",
                "Specify format (e.g., email, phone, date format)",
                "Specify allowed values or patterns",
                "No additional validation needed"
            ],
            answer=None,
            answered_by=None,
            answered_at=None
        ))
    
    # Check for potential PII/sensitive data
    if _might_contain_pii(column):
        questions.append(ContractQuestion(
            question_id=_generate_question_id(),
            question=f"Does '{column.name}' contain sensitive or personal data?",
            context=f"The column '{column.name}' may contain sensitive information based on its name. Please classify its data sensitivity level.",
            suggested_answers=[
                "Public - no sensitive data",
                "Internal - company confidential",
                "PII - personally identifiable information",
                "Highly Sensitive - requires special protection"
            ],
            answer=None,
            answered_by=None,
            answered_at=None
        ))
    
    return questions


def detect_relationship_ambiguities(
    fk: ForeignKeyConstraint,
    table: TableSchema
) -> List[ContractQuestion]:
    """
    Detect ambiguities in foreign key relationships.
    
    Args:
        fk: Foreign key constraint to analyze
        table: Table schema containing the foreign key
        
    Returns:
        List of questions needing human clarification
    """
    questions = []
    
    # Ask about the business meaning of the relationship
    questions.append(ContractQuestion(
        question_id=_generate_question_id(),
        question=f"What business relationship does '{fk.column_name}' represent?",
        context=f"The column '{fk.column_name}' in table '{table.table_name}' references '{fk.referenced_table}.{fk.referenced_column}'. Please describe this relationship in business terms.",
        suggested_answers=[
            f"Each {table.table_name} belongs to one {fk.referenced_table}",
            f"Each {table.table_name} is associated with a {fk.referenced_table}",
            "Provide custom business description"
        ],
        answer=None,
        answered_by=None,
        answered_at=None
    ))
    
    # Check for missing ON DELETE/UPDATE actions
    if not fk.on_delete:
        questions.append(ContractQuestion(
            question_id=_generate_question_id(),
            question=f"What should happen when the referenced {fk.referenced_table} is deleted?",
            context=f"The foreign key '{fk.column_name}' doesn't specify an ON DELETE action. Please clarify the desired behavior.",
            suggested_answers=[
                "CASCADE - delete this record too",
                "SET NULL - set this field to NULL",
                "RESTRICT - prevent deletion of referenced record",
                "NO ACTION - database default behavior"
            ],
            answer=None,
            answered_by=None,
            answered_at=None
        ))
    
    return questions


def detect_business_rule_gaps(table: TableSchema) -> List[ContractQuestion]:
    """
    Detect potential business rules that should be documented.
    
    Args:
        table: Table schema to analyze
        
    Returns:
        List of questions about business rules
    """
    questions = []
    
    # Check for numeric columns that might have range constraints
    numeric_columns = [
        col for col in table.columns
        if any(t in col.data_type.lower() for t in ['int', 'numeric', 'decimal', 'real', 'double', 'float'])
        and not col.primary_key
    ]
    
    for col in numeric_columns:
        if 'rate' in col.name.lower() or 'price' in col.name.lower() or 'amount' in col.name.lower():
            questions.append(ContractQuestion(
                question_id=_generate_question_id(),
                question=f"What are the valid ranges for '{col.name}'?",
                context=f"The numeric column '{col.name}' likely has business-defined min/max values. Please specify acceptable ranges.",
                suggested_answers=[
                    "Specify minimum and maximum values",
                    "Must be positive (> 0)",
                    "Must be non-negative (>= 0)",
                    "No specific range constraints"
                ],
                answer=None,
                answered_by=None,
                answered_at=None
            ))
    
    # Check for date columns that might have constraints
    date_columns = [
        col for col in table.columns
        if any(t in col.data_type.lower() for t in ['date', 'time', 'timestamp'])
        and col.name.lower() not in ['created_at', 'updated_at', 'last_update']
    ]
    
    for col in date_columns:
        questions.append(ContractQuestion(
            question_id=_generate_question_id(),
            question=f"Are there any date constraints for '{col.name}'?",
            context=f"The date column '{col.name}' may have business rules about valid date ranges. Please specify any constraints.",
            suggested_answers=[
                "Must be in the past",
                "Must be in the future",
                "Must be within specific date range",
                "No date constraints"
            ],
            answer=None,
            answered_by=None,
            answered_at=None
        ))
    
    # Check for status/type columns that might be enums
    potential_enum_columns = [
        col for col in table.columns
        if any(keyword in col.name.lower() for keyword in ['status', 'type', 'category', 'state', 'kind'])
    ]
    
    for col in potential_enum_columns:
        questions.append(ContractQuestion(
            question_id=_generate_question_id(),
            question=f"What are the valid values for '{col.name}'?",
            context=f"The column '{col.name}' appears to be a status/type field. Please list all valid values and their meanings.",
            suggested_answers=[
                "Provide comma-separated list of valid values",
                "Describe each status/type and its meaning",
                "No fixed set of values"
            ],
            answer=None,
            answered_by=None,
            answered_at=None
        ))
    
    return questions


def detect_data_sensitivity_questions(table: TableSchema) -> List[ContractQuestion]:
    """
    Detect questions about data sensitivity and access control.
    
    Args:
        table: Table schema to analyze
        
    Returns:
        List of questions about data sensitivity
    """
    questions = []
    
    # Ask about overall table sensitivity
    questions.append(ContractQuestion(
        question_id=_generate_question_id(),
        question=f"What is the overall data sensitivity level for the '{table.table_name}' table?",
        context=f"Please classify the sensitivity of data in the '{table.table_name}' table to determine appropriate access controls.",
        suggested_answers=[
            "Public - can be shared externally",
            "Internal - company employees only",
            "Confidential - restricted access",
            "Highly Sensitive - requires special approval"
        ],
        answer=None,
        answered_by=None,
        answered_at=None
    ))
    
    # Ask about data retention
    questions.append(ContractQuestion(
        question_id=_generate_question_id(),
        question=f"What is the data retention policy for '{table.table_name}'?",
        context=f"Please specify how long data in '{table.table_name}' should be retained and when it should be archived or deleted.",
        suggested_answers=[
            "Retain indefinitely",
            "Retain for specific period (specify duration)",
            "Archive after specific period",
            "Delete after specific period"
        ],
        answer=None,
        answered_by=None,
        answered_at=None
    ))
    
    return questions


def detect_all_ambiguities(table: TableSchema) -> List[ContractQuestion]:
    """
    Run all ambiguity detection checks on a table.
    
    Args:
        table: Table schema to analyze
        
    Returns:
        Complete list of questions needing human review
    """
    all_questions = []
    
    # Detect column-level ambiguities
    for column in table.columns:
        column_questions = detect_column_ambiguities(column, table.table_name)
        all_questions.extend(column_questions)
    
    # Detect relationship ambiguities
    for fk in table.foreign_keys:
        fk_questions = detect_relationship_ambiguities(fk, table)
        all_questions.extend(fk_questions)
    
    # Detect business rule gaps
    business_questions = detect_business_rule_gaps(table)
    all_questions.extend(business_questions)
    
    # Detect data sensitivity questions
    sensitivity_questions = detect_data_sensitivity_questions(table)
    all_questions.extend(sensitivity_questions)
    
    # Prioritize questions
    all_questions = _prioritize_questions(all_questions)
    
    # Limit to top questions to avoid overwhelming users
    max_questions = 10
    if len(all_questions) > max_questions:
        all_questions = all_questions[:max_questions]
    
    return all_questions


def _generate_question_id() -> str:
    """Generate a unique question ID."""
    return f"q_{uuid.uuid4().hex[:12]}"


def _needs_validation_rule(column: ColumnSchema) -> bool:
    """Check if a column likely needs validation rules."""
    # Skip primary keys and foreign keys
    if column.primary_key or column.foreign_key:
        return False
    
    # Skip auto-generated columns
    if column.auto_increment or column.name.lower() in ['created_at', 'updated_at', 'last_update']:
        return False
    
    # Check if data type commonly needs validation
    data_type_lower = column.data_type.lower()
    needs_validation = any(t in data_type_lower for t in VALIDATION_PRONE_TYPES)
    
    # Additional check for string columns without max length
    if 'varchar' in data_type_lower or 'text' in data_type_lower:
        if not column.max_length and 'text' not in data_type_lower:
            return True
    
    return needs_validation


def _might_contain_pii(column: ColumnSchema) -> bool:
    """Check if a column might contain PII based on name."""
    column_name_lower = column.name.lower()
    return any(keyword in column_name_lower for keyword in POTENTIAL_PII_KEYWORDS)


def _prioritize_questions(questions: List[ContractQuestion]) -> List[ContractQuestion]:
    """
    Prioritize questions by importance.
    
    Priority order:
    1. Data sensitivity questions (security/compliance)
    2. Business rule questions (data quality)
    3. Relationship questions (data integrity)
    4. Column meaning questions (documentation)
    """
    priority_keywords = {
        'high': ['sensitive', 'personal', 'pii', 'security', 'retention'],
        'medium': ['validation', 'range', 'constraint', 'business', 'relationship'],
        'low': ['represent', 'mean', 'describe']
    }
    
    def get_priority(question: ContractQuestion) -> int:
        question_lower = question.question.lower()
        
        if any(keyword in question_lower for keyword in priority_keywords['high']):
            return 1
        elif any(keyword in question_lower for keyword in priority_keywords['medium']):
            return 2
        else:
            return 3
    
    # Sort by priority (lower number = higher priority)
    sorted_questions = sorted(questions, key=get_priority)
    
    return sorted_questions


# Made with Bob