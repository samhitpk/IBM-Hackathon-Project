"""
Contract Service Layer for DataContractIQ
Business logic for contract operations
"""
import logging
from typing import List, Optional, Dict
from datetime import datetime

from app.models.contract import DataContract, ContractStatus, ContractQuestion, BusinessRule
from app.core.contract_storage import (
    contract_storage,
    load_contract as storage_load_contract,
    save_contract as storage_save_contract
)
from app.api.models import QuestionAnswer, ContractSummary

logger = logging.getLogger(__name__)


def get_contracts_list(
    status: Optional[str] = None,
    table_name: Optional[str] = None
) -> List[ContractSummary]:
    """
    Get list of contracts with summary information.
    
    Args:
        status: Filter by status (draft/approved)
        table_name: Filter by table name
        
    Returns:
        List of contract summaries
    """
    # Convert status string to enum if provided
    status_enum = None
    if status:
        try:
            status_enum = ContractStatus(status.lower())
        except ValueError:
            logger.warning(f"Invalid status filter: {status}")
            status_enum = None
    
    # Get contracts from storage
    contracts_data = contract_storage.list_contracts(
        status=status_enum,
        table_name=table_name
    )
    
    # Convert to summary format
    summaries = []
    for contract_data in contracts_data:
        # Load full contract to count questions
        try:
            contract = storage_load_contract(contract_data["contract_id"])
            
            total_questions = len(contract.questions)
            unanswered = sum(1 for q in contract.questions if not q.answer)
            
            summary = ContractSummary(
                contract_id=contract_data["contract_id"],
                table_name=contract_data["table_name"],
                schema_name=contract_data.get("schema_name", "public"),
                status=contract_data["status"],
                created_at=contract_data["created_at"],
                updated_at=contract_data.get("updated_at"),
                approved_at=contract_data.get("approved_at"),
                approved_by=contract_data.get("approved_by"),
                total_questions=total_questions,
                unanswered_questions=unanswered,
                confidence_score=contract.metadata.confidence_score
            )
            summaries.append(summary)
        except Exception as e:
            logger.error(f"Error loading contract {contract_data['contract_id']}: {e}")
            continue
    
    return summaries


def get_contract_details(contract_id: str) -> DataContract:
    """
    Get full contract details.
    
    Args:
        contract_id: Contract identifier
        
    Returns:
        Complete contract data
        
    Raises:
        FileNotFoundError: If contract doesn't exist
    """
    return storage_load_contract(contract_id)


def update_contract_answers(
    contract_id: str,
    answers: List[QuestionAnswer]
) -> DataContract:
    """
    Update contract with question answers.
    
    Args:
        contract_id: Contract to update
        answers: List of question answers
        
    Returns:
        Updated contract
        
    Raises:
        FileNotFoundError: If contract doesn't exist
        ValueError: If question ID not found
    """
    # Load contract
    contract = storage_load_contract(contract_id)
    
    # Update each answer
    for answer_data in answers:
        question_found = False
        for question in contract.questions:
            if question.question_id == answer_data.question_id:
                question.answer = answer_data.answer
                question.answered_by = answer_data.answered_by
                question.answered_at = datetime.utcnow()
                question_found = True
                break
        
        if not question_found:
            raise ValueError(f"Question ID not found: {answer_data.question_id}")
    
    # Update contract metadata
    contract.metadata.updated_at = datetime.utcnow()
    
    # Recalculate confidence score based on answered questions
    if contract.questions:
        answered_count = sum(1 for q in contract.questions if q.answer)
        answer_ratio = answered_count / len(contract.questions)
        # Boost confidence by up to 20% based on answered questions
        confidence_boost = answer_ratio * 0.2
        current_score = contract.metadata.confidence_score or 0.7
        contract.metadata.confidence_score = min(0.95, current_score + confidence_boost)
    
    # Save updated contract
    saved_contract = storage_save_contract(contract)
    
    logger.info(f"Updated {len(answers)} answers for contract {contract_id}")
    
    return saved_contract


def approve_contract(
    contract_id: str,
    approved_by: str,
    notes: Optional[str] = None
) -> DataContract:
    """
    Approve a contract and merge AI + human insights.
    
    Args:
        contract_id: Contract to approve
        approved_by: User approving the contract
        notes: Approval notes
        
    Returns:
        Approved contract with merged insights
        
    Raises:
        FileNotFoundError: If contract doesn't exist
    """
    # Load contract
    contract = storage_load_contract(contract_id)
    
    # MVP: No validation required - questions are optional
    logger.info(f"Approving contract {contract_id} (questions optional for MVP)")
    
    # Merge AI-generated content with human answers
    contract = merge_ai_and_human_insights(contract)
    
    # Update status to approved
    contract.metadata.status = ContractStatus.APPROVED
    contract.metadata.approved_by = approved_by
    contract.metadata.approved_at = datetime.utcnow()
    contract.metadata.updated_at = datetime.utcnow()
    
    if notes:
        contract.metadata.approval_notes = notes
    
    # Save approved contract
    saved_contract = storage_save_contract(contract)
    
    logger.info(f"Contract {contract_id} approved by {approved_by}")
    
    return saved_contract


def merge_ai_and_human_insights(contract: DataContract) -> DataContract:
    """
    Merge AI-extracted technical details with human business context.
    
    Args:
        contract: Contract to enhance
        
    Returns:
        Contract with merged insights
    """
    logger.info(f"Merging AI + human insights for contract {contract.metadata.contract_id}")
    
    # Process each answered question
    for question in contract.questions:
        if not question.answer:
            continue  # Skip unanswered questions (MVP allows this)
        
        question_lower = question.question.lower()
        
        # Enhance column descriptions with business context
        if "represent" in question_lower or "mean" in question_lower:
            # Find the column mentioned in the question
            for column in contract.columns:
                if column.name in question.question:
                    # Enhance description with human answer
                    if "Technical:" not in column.description:
                        original_desc = column.description
                        column.description = f"{question.answer} (Technical: {original_desc})"
                    break
        
        # Add business rules from answers
        elif "validation" in question_lower or "range" in question_lower or "constraint" in question_lower:
            if "no" not in question.answer.lower() and "none" not in question.answer.lower():
                # Create business rule from answer
                rule = BusinessRule(
                    rule_id=f"rule_{question.question_id}",
                    description=question.answer,
                    rule_type="validation",
                    enforcement="application",
                    sql_expression=None,
                    examples=[],
                    exceptions=[]
                )
                contract.business_rules.append(rule)
        
        # Update data sensitivity
        elif "sensitive" in question_lower or "pii" in question_lower:
            # Find column and update sensitivity
            for column in contract.columns:
                if column.name in question.question:
                    column.sensitivity = question.answer
                    break
            
            # Also update table-level access control if it's about overall sensitivity
            if "overall" in question_lower or "table" in question_lower:
                contract.access_control = question.answer
        
        # Update data retention policy
        elif "retention" in question_lower:
            contract.data_retention = question.answer
        
        # Enhance relationship descriptions
        elif "relationship" in question_lower:
            for rel in contract.relationships:
                if rel.column in question.question:
                    # Enhance with business context
                    if "Technical:" not in rel.description:
                        original_desc = rel.description
                        rel.description = f"{question.answer} (Technical: {original_desc})"
                    break
        
        # Add valid values for enum-like columns
        elif "valid values" in question_lower:
            for column in contract.columns:
                if column.name in question.question:
                    # Parse comma-separated values
                    if "," in question.answer:
                        values = [v.strip() for v in question.answer.split(",")]
                        column.valid_values = values
                    break
    
    # Boost confidence score after merging insights
    answered_count = sum(1 for q in contract.questions if q.answer)
    if answered_count > 0:
        current_score = contract.metadata.confidence_score or 0.7
        contract.metadata.confidence_score = min(0.95, current_score + 0.1)
    
    logger.info(f"Merged {answered_count} answered questions into contract")
    
    return contract


# Made with Bob