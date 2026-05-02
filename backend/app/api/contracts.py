"""
Contracts API Router for DataContractIQ
Endpoints for contract management and approval workflow
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.api.models import (
    ContractSummary,
    AnswersSubmission,
    ApprovalRequest,
    ContractResponse,
    ErrorResponse
)
from app.models.contract import DataContract, DriftDetectionResponse
from app.services import contract_service
from app.services import drift_service
from app.core.contract_formatter import contract_to_markdown

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/contracts",
    response_model=List[ContractSummary],
    summary="List all contracts",
    description="Get a list of all contracts with optional filtering by status or table name"
)
async def list_contracts(
    status: Optional[str] = Query(None, description="Filter by status (draft/approved)"),
    table_name: Optional[str] = Query(None, description="Filter by table name")
):
    """
    List all contracts with summary information.
    
    Query Parameters:
    - status: Filter by contract status (draft, approved)
    - table_name: Filter by specific table name
    
    Returns:
    - List of contract summaries with question counts
    """
    try:
        summaries = contract_service.get_contracts_list(
            status=status,
            table_name=table_name
        )
        return summaries
    except Exception as e:
        logger.error(f"Error listing contracts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/contracts/{contract_id}",
    response_model=DataContract,
    summary="Get contract details",
    description="Get complete details for a specific contract including all questions"
)
async def get_contract(contract_id: str):
    """
    Get full contract details.
    
    Path Parameters:
    - contract_id: Unique contract identifier
    
    Returns:
    - Complete contract data including columns, relationships, and questions
    """
    try:
        contract = contract_service.get_contract_details(contract_id)
        return contract
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Contract not found: {contract_id}")
    except Exception as e:
        logger.error(f"Error getting contract {contract_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/contracts/{contract_id}/markdown",
    response_class=PlainTextResponse,
    summary="Get contract as Markdown",
    description="Get contract formatted as human-readable Markdown"
)
async def get_contract_markdown(contract_id: str):
    """
    Get contract in Markdown format.
    
    Path Parameters:
    - contract_id: Unique contract identifier
    
    Returns:
    - Contract formatted as Markdown text
    """
    try:
        contract = contract_service.get_contract_details(contract_id)
        markdown = contract_to_markdown(contract)
        return markdown
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Contract not found: {contract_id}")
    except Exception as e:
        logger.error(f"Error getting contract markdown {contract_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/contracts/{contract_id}/answers",
    response_model=DataContract,
    summary="Submit question answers",
    description="Submit answers to contract questions (answers are optional for MVP)"
)
async def submit_answers(contract_id: str, submission: AnswersSubmission):
    """
    Submit answers to contract questions.
    
    Path Parameters:
    - contract_id: Contract to update
    
    Request Body:
    - answers: List of question answers with question_id, answer, and answered_by
    
    Returns:
    - Updated contract with answers
    
    Note: For MVP, answering questions is optional. Users can approve without answering all questions.
    """
    try:
        updated_contract = contract_service.update_contract_answers(
            contract_id=contract_id,
            answers=submission.answers
        )
        return updated_contract
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Contract not found: {contract_id}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting answers for {contract_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/contracts/{contract_id}/approve",
    response_model=ContractResponse,
    summary="Approve contract with answers",
    description="Approve a contract and save answers in one action (MVP: no validation required)"
)
async def approve_contract(contract_id: str, approval: ApprovalRequest):
    """
    Approve a contract with optional answers.
    
    Path Parameters:
    - contract_id: Contract to approve
    
    Request Body:
    - approved_by: User approving the contract
    - notes: Optional approval notes
    - answers: Optional list of question answers
    
    Returns:
    - Success response with contract ID
    
    Note: For MVP, questions are optional. Answers are saved alongside the contract.
    """
    try:
        approved_contract = contract_service.approve_contract(
            contract_id=contract_id,
            approved_by=approval.approved_by,
            notes=approval.notes,
            answers=approval.answers
        )
        
        return ContractResponse(
            success=True,
            message=f"Contract approved successfully for table '{approved_contract.table_name}'",
            contract_id=approved_contract.metadata.contract_id
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Contract not found: {contract_id}")
    except Exception as e:
        logger.error(f"Error approving contract {contract_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/contracts/stats/summary",
    summary="Get contract statistics",
    description="Get summary statistics about all contracts"
)
async def get_contract_stats():
    """
    Get contract statistics.
    
    Returns:
    - Summary statistics including counts by status, total questions, etc.
    """
    try:
        all_contracts = contract_service.get_contracts_list()
        
        stats = {
            "total_contracts": len(all_contracts),
            "by_status": {
                "draft": sum(1 for c in all_contracts if c.status == "draft"),
                "approved": sum(1 for c in all_contracts if c.status == "approved")
            },
            "total_questions": sum(c.total_questions for c in all_contracts),
            "unanswered_questions": sum(c.unanswered_questions for c in all_contracts),
            "tables_covered": list(set(c.table_name for c in all_contracts))
        }
        
        return stats
    except Exception as e:
        logger.error(f"Error getting contract stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Made with Bob

@router.get(
    "/drift/{table_name}",
    response_model=DriftDetectionResponse,
    summary="Detect schema drift for a table",
    description="Compare current database schema against approved contract to detect changes"
)
async def detect_drift(table_name: str):
    """
    Detect schema drift for a specific table.
    
    Path Parameters:
    - table_name: Table to check for drift
    
    Returns:
    - Detailed drift report with all detected changes
    """
    try:
        drift_response = drift_service.detect_drift_for_table(table_name)
        return drift_response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error detecting drift for {table_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/drift/summary/all",
    summary="Get drift summary for all approved contracts",
    description="Check drift status across all tables with approved contracts"
)
async def get_drift_summary():
    """
    Get summary of drift status for all monitored tables.
    
    Returns:
    - Summary statistics including tables with drift, change counts by severity
    """
    try:
        summary = drift_service.get_drift_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting drift summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

