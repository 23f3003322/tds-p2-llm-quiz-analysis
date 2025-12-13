from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class AnswerResult(BaseModel):
    """Structured output from answer generation"""
    
    answer: str = Field(
        description="The exact answer to submit (final output)"
    )
    
    reasoning: str = Field(
        description="Step-by-step explanation of how answer was generated"
    )
    
    components_used: Dict[str, Any] = Field(
        default_factory=dict,
        description="Which components from analysis were used"
    )
    
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in answer correctness (0.0-1.0)"
    )
    
    personalization_applied: bool = Field(
        default=False,
        description="Whether personalization was applied"
    )
    
    validation_notes: str = Field(
        default="",
        description="Notes about format validation"
    )
