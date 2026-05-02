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
from app.models.contract import DataContract
from app.services import contract_service
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
    summary="Approve contract",
    description="Approve a contract and merge AI insights with human answers (no validation required for MVP)"
)
async def approve_contract(contract_id: str, approval: ApprovalRequest):
    """
    Approve a contract.
    
    Path Parameters:
    - contract_id: Contract to approve
    
    Request Body:
    - approved_by: User approving the contract
    - notes: Optional approval notes
    
    Returns:
    - Success response with contract ID
    
    Note: For MVP, questions are optional. Users can approve contracts with unanswered questions.
    The system will merge any answered questions with AI-generated content.
    """
    try:
        approved_contract = contract_service.approve_contract(
            contract_id=contract_id,
            approved_by=approval.approved_by,
            notes=approval.notes
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