from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Literal

class QuestionAnalysis(BaseModel):
    """
    Analysis focused on generating the correct answer.
    No redirect/entry page logic needed.
    """
    
    # ===== QUESTION CLASSIFICATION =====
    question_type: Literal[
        'cli_command',           # Q2, Q3: shell commands
        'file_path',             # Q4: paths/URLs
        'data_processing',       # Q7, Q9, Q11: CSV/JSON processing
        'image_analysis',        # Q6, Q17: image operations
        'audio_transcription',   # Q5: audio to text
        'api_interaction',       # Q8: external API calls
        'document_parsing',      # Q10: PDF extraction
        'calculation',           # Q20, Q21: mathematical computations
        'text_generation',       # Q12, Q13, Q19: YAML, prompts
        'optimization',          # Q14, Q18: constraint solving
        'llm_reasoning'          # Q16: tool planning/reasoning
    ] = Field(description="Type of task to solve")
    
    # ===== ANSWER FORMAT =====
    answer_format: Literal[
        'plain_string',          # Q2, Q3, Q4: raw text
        'json_object',           # Q11, Q14, Q16, Q21: {"key": "value"}
        'json_array',            # Q20: ["a", "b", "c"]
        'number',                # Q8, Q9, Q10, Q17, Q18: integer/float
        'single_letter'          # Q12: A, B, or C
    ] = Field(description="How to format the final answer")
    
    # ===== ANSWER COMPONENTS =====
    key_components: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted components needed to generate answer"
    )
    
    # ===== PERSONALIZATION =====
    requires_personalization: bool = Field(
        default=False,
        description="Does answer depend on user email?"
    )
    
    personalization_type: Optional[Literal[
        'email_in_url',          # Q2: ?email=<user_email>
        'email_length_offset',   # Q8, Q9, Q15, Q18: offset = len(email) mod N
        'email_length_conditional'  # Q15: if even/odd
    ]] = None
    
    personalization_details: Optional[str] = Field(
        default=None,
        description="Specific personalization logic"
    )
    
    # ===== FILE REQUIREMENTS =====
    requires_files: bool = Field(
        default=False,
        description="Does question need file downloads?"
    )
    
    required_file_types: List[str] = Field(
        default_factory=list,
        description="File types needed: csv, json, png, pdf, opus, zip"
    )
    
    # ===== EXTERNAL RESOURCES =====
    requires_external_fetch: bool = Field(
        default=False,
        description="Need to fetch data from another URL (not just files)?"
    )
    
    external_resources: List[str] = Field(
        default_factory=list,
        description="URLs/endpoints to fetch before solving"
    )
    
    # ===== CRITICAL CONSTRAINTS =====
    critical_constraints: List[str] = Field(
        default_factory=list,
        description="Must-follow rules for answer format"
    )
    
    # ===== SUBMISSION INFO =====
    submission_url_path: str = Field(
        description="URL path for this question (e.g., '/project2-uv')"
    )
    
    # ===== CONFIDENCE & REASONING =====
    reasoning: str = Field(
        description="Why this classification and components were chosen"
    )
    
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in analysis (0.0-1.0)"
    )
