from typing import Dict, Any, List
from app.core.logging import get_logger
from app.core.exceptions import TaskProcessingError
from app.models.analysis import QuestionAnalysis
from app.utils.prompts import AnalysisPrompts
logger = get_logger(__name__)


class QuestionAnalyzer:
    """
    Analyzes questions to determine how to generate answers.
    No entry page or redirect logic - assumes all content is solvable questions.
    """
    
    def __init__(self, llm_client):
        """
        Args:
            llm_client: LLM client with run_agent() method
        """
        self.llm_client = llm_client
        self._analyzer_agent = None
    
    async def initialize(self):
        """Initialize LLM agent"""
        self._analyzer_agent = self.llm_client.create_agent(
            output_type=QuestionAnalysis,
            system_prompt=(
                "You are an expert at analyzing technical quiz questions. "
                "Extract precise information needed to generate correct answers. "
                "Be thorough and accurate."
            ),
            retries=2
        )
        logger.info("✓ Question analyzer initialized")
    
    async def analyze_question(
        self,
        question_metadata: Dict[str, Any],
        base_url: str,
        user_email: str,
        downloaded_files: List[Dict[str, Any]]
    ) -> QuestionAnalysis:
        """
        Analyze question to determine how to generate the answer.
        
        Args:
            question_metadata: Parsed metadata from scraping
                - title: Question title
                - heading: Question heading
                - difficulty: 1-5
                - is_personalized: bool
                - instructions: List of instruction strings
                - file_links: List of file references
            base_url: Base URL for the quiz
            user_email: User's email address
            downloaded_files: List of downloaded file info
                - filename, type, path, size
        
        Returns:
            QuestionAnalysis: Structured analysis
        
        Raises:
            TaskProcessingError: If analysis fails
        """
        logger.info(f"🤖 Analyzing question: {question_metadata.get('title', 'unknown')}")
        
        # Build prompt
        prompt = AnalysisPrompts.question_analysis_prompt(
            instructions=question_metadata.get('instructions', []),
            difficulty=question_metadata.get('difficulty', 1),
            is_personalized=question_metadata.get('is_personalized', False),
            title=question_metadata.get('title', ''),
            heading=question_metadata.get('heading', ''),
            base_url=base_url,
            user_email=user_email,
            available_files=downloaded_files
        )
        
        try:
            # Run LLM analysis
            analysis: QuestionAnalysis = await self.llm_client.run_agent(
                self._analyzer_agent,
                prompt
            )
            
            # Log analysis results
            logger.info(f"✓ Question type: {analysis.question_type}")
            logger.info(f"✓ Answer format: {analysis.answer_format}")
            logger.info(f"✓ Personalization: {analysis.requires_personalization}")
            logger.info(f"✓ Files needed: {analysis.requires_files}")
            logger.info(f"✓ Confidence: {analysis.confidence:.2f}")
            
            # Validate analysis
            self._validate_analysis(analysis, question_metadata)
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Question analysis failed: {e}", exc_info=True)
            raise TaskProcessingError(
                f"Cannot analyze question: {str(e)}. "
                "LLM analysis is required for unknown question types."
            )
    
    def _validate_analysis(
        self,
        analysis: QuestionAnalysis,
        metadata: Dict[str, Any]
    ):
        """
        Validate analysis results make sense.
        
        Args:
            analysis: LLM analysis result
            metadata: Original question metadata
        
        Raises:
            TaskProcessingError: If validation fails
        """
        # Check confidence threshold
        if analysis.confidence < 0.5:
            logger.warning(
                f"⚠️ Low confidence analysis: {analysis.confidence:.2f}"
            )
        
        # Check personalization consistency
        if metadata.get('is_personalized') and not analysis.requires_personalization:
            logger.warning(
                "⚠️ Metadata says personalized but analysis disagrees"
            )
        
        # Check file requirements
        if analysis.requires_files and not analysis.required_file_types:
            logger.warning(
                "⚠️ Requires files but no file types specified"
            )
        
        # Check submission URL
        if not analysis.submission_url_path:
            raise TaskProcessingError(
                "Analysis missing submission_url_path"
            )
        
        if not analysis.submission_url_path.startswith('/'):
            logger.warning(
                f"⚠️ Submission URL should start with '/': {analysis.submission_url_path}"
            )
        
        logger.debug("✓ Analysis validation passed")
