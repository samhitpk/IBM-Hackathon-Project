"""
API Request/Response Models for DataContractIQ
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ContractSummary(BaseModel):
    """Summary information for contract list view"""
    contract_id: str = Field(..., description="Unique contract identifier")
    table_name: str = Field(..., description="Table name")
    schema_name: str = Field(default="public", description="Schema name")
    status: str = Field(..., description="Contract status (draft/approved)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    approved_by: Optional[str] = Field(None, description="Who approved")
    total_questions: int = Field(default=0, description="Total number of questions")
    unanswered_questions: int = Field(default=0, description="Number of unanswered questions")
    confidence_score: Optional[float] = Field(None, description="AI confidence score")


class QuestionAnswer(BaseModel):
    """Answer to a contract question"""
    question_id: str = Field(..., description="Question identifier")
    answer: str = Field(..., description="User's answer")
    answered_by: str = Field(..., description="Who answered the question")


class AnswersSubmission(BaseModel):
    """Batch submission of question answers"""
    answers: List[QuestionAnswer] = Field(..., description="List of answers")


class ApprovalRequest(BaseModel):
    """Request to approve a contract"""
    approved_by: str = Field(..., description="User approving the contract")
    notes: Optional[str] = Field(None, description="Approval notes")


class ContractResponse(BaseModel):
    """Response after contract operation"""
    success: bool = Field(..., description="Whether operation succeeded")
    message: str = Field(..., description="Result message")
    contract_id: Optional[str] = Field(None, description="Contract ID")
    

class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")


# Made with Bob