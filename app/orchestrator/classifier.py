"""
Task Classifier
Intelligent classification of tasks using LLM with Pydantic AI
"""

from typing import Dict, Any, Optional
import pydantic_ai
print(pydantic_ai.__file__)

from pydantic_ai import Agent

from app.orchestrator.models import (
    TaskClassification,
    ContentAnalysis,
    TaskType
)
from app.utils.llm_client import get_llm_client
from app.utils.prompts import SystemPrompts, PromptTemplates
from app.core.logging import get_logger
from app.core.exceptions import TaskProcessingError

logger = get_logger(__name__)


class TaskClassifier:
    """
    Intelligent task classifier using LLM
    Analyzes task descriptions and classifies them into structured categories
    """
    
    def __init__(self):
        """Initialize task classifier"""
        self.llm_client = get_llm_client()
        
        # Create classification agent
        self._classification_agent = self.llm_client.create_agent(
            output_type=TaskClassification,
            system_prompt=SystemPrompts.CLASSIFIER,
            retries=2
        )
        
        # Create content analysis agent
        self._content_agent = self.llm_client.create_agent(
            output_type=ContentAnalysis,
            system_prompt=SystemPrompts.CONTENT_ANALYZER,
            retries=2
        )
        
        logger.debug("TaskClassifier initialized with Pydantic AI agents")
    
    async def analyze_content(
        self,
        task_info: Dict[str, Any]
    ) -> ContentAnalysis:
        """
        Analyze fetched content to determine if it's the actual task
        or requires additional actions
        
        Args:
            task_info: Output from TaskFetcher with content and metadata
            
        Returns:
            ContentAnalysis: Structured analysis of the content
            
        Raises:
            TaskProcessingError: If analysis fails
        """
        logger.info("🔍 Analyzing content to determine if it's the actual task")
        
        try:
            # Build prompt from task_info
            prompt = PromptTemplates.content_analyzer(
                url=task_info.get('url', ''),
                content_type=task_info.get('content_type', ''),
                content_preview=task_info.get('task_description', ''),
                special_elements=task_info.get('metadata', {}).get('special_elements', {})
            )
            
            logger.debug(f"Content analysis prompt length: {len(prompt)} chars")
            
            # Run content analysis agent
            analysis = await self.llm_client.run_agent(
                self._content_agent,
                prompt
            )
            
            logger.info(
                f"✅ Content analysis complete | "
                f"Direct task: {analysis.is_direct_task} | "
                f"Confidence: {analysis.confidence:.2f}"
            )
            
            if analysis.is_direct_task:
                logger.info("Content is ready-to-use task description")
            else:
                logger.warning(
                    f"Content requires additional actions: "
                    f"download={analysis.requires_download}, "
                    f"transcription={analysis.requires_transcription}, "
                    f"OCR={analysis.requires_ocr}, "
                    f"navigation={analysis.requires_navigation}"
                )
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Content analysis failed: {str(e)}", exc_info=True)
            raise TaskProcessingError(f"Failed to analyze content: {str(e)}")
    
    async def classify_task(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TaskClassification:
        """
        Classify a task description into structured categories
        
        Args:
            task_description: The task to classify
            context: Optional additional context (metadata, URLs, etc.)
            
        Returns:
            TaskClassification: Structured classification with validation
            
        Raises:
            TaskProcessingError: If classification fails
        """
        logger.info("🏷️  Classifying task")
        logger.debug(f"Task description: {task_description[:200]}...")
        
        try:
            # Build classification prompt
            prompt = PromptTemplates.task_classifier(task_description)
            
            # Add context if provided
            if context:
                context_info = self._format_context(context)
                prompt += f"\n\nAdditional Context:\n{context_info}"
            
            logger.debug(f"Classification prompt length: {len(prompt)} chars")
            
            # Run classification agent
            classification = await self.llm_client.run_agent(
                self._classification_agent,
                prompt
            )
            
            # Log classification results
            logger.info(
                f"✅ Task classified | "
                f"Primary: {classification.primary_task.value} | "
                f"Complexity: {classification.complexity.value} | "
                f"Steps: {classification.estimated_steps} | "
                f"Confidence: {classification.confidence:.2f}"
            )
            
            if classification.secondary_tasks:
                secondary = [t.value for t in classification.secondary_tasks]
                logger.info(f"Secondary tasks: {', '.join(secondary)}")
            
            if classification.key_entities:
                logger.debug(f"Key entities: {classification.key_entities}")
            
            if classification.suggested_tools:
                logger.info(f"Suggested tools: {', '.join(classification.suggested_tools)}")
            
            # Log warnings for special requirements
            if classification.requires_javascript:
                logger.warning("⚠️  Task requires JavaScript rendering")
            
            if classification.requires_authentication:
                logger.warning("⚠️  Task requires authentication/API keys")
            
            if classification.requires_external_data:
                logger.warning("⚠️  Task requires external data sources")
            
            return classification
            
        except Exception as e:
            logger.error(f"❌ Task classification failed: {str(e)}", exc_info=True)
            raise TaskProcessingError(f"Failed to classify task: {str(e)}")
    
    async def classify_with_content_check(
        self,
        task_info: Dict[str, Any]
    ) -> tuple[Optional[ContentAnalysis], TaskClassification]:
        """
        Complete classification pipeline:
        1. Analyze if content needs additional processing
        2. Classify the actual task
        
        Args:
            task_info: Output from TaskFetcher
            
        Returns:
            tuple: (ContentAnalysis or None, TaskClassification)
        """
        logger.info("🔄 Starting complete classification pipeline")
        
        content_analysis = None
        task_description = task_info.get('task_description', '')
        
        # Step 1: Check if content needs LLM analysis
        if task_info.get('needs_llm_analysis', False):
            logger.info("Step 1: Content requires LLM analysis")
            content_analysis = await self.analyze_content(task_info)
            
            # If not a direct task, we might need to process it first
            if not content_analysis.is_direct_task:
                logger.warning(
                    "Content is not a direct task. Additional processing needed."
                )
                # For now, we'll still try to classify what we have
                # In future steps, we'll add action execution here
                
                # If LLM extracted a better task description, use it
                if content_analysis.task_description:
                    task_description = content_analysis.task_description
        else:
            logger.info("Step 1: Content is straightforward, skipping analysis")
        
        # Step 2: Classify the task
        logger.info("Step 2: Classifying task")
        
        # Prepare context from metadata
        context = {
            'url': task_info.get('url'),
            'content_type': task_info.get('content_type'),
            'metadata': task_info.get('metadata', {})
        }
        
        classification = await self.classify_task(task_description, context)
        
        logger.info("✅ Complete classification pipeline finished")
        
        return content_analysis, classification
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        Format context dictionary into readable text for LLM
        
        Args:
            context: Context dictionary
            
        Returns:
            str: Formatted context
        """
        lines = []
        
        if context.get('url'):
            lines.append(f"Source URL: {context['url']}")
        
        if context.get('content_type'):
            lines.append(f"Content Type: {context['content_type']}")
        
        metadata = context.get('metadata', {})
        
        if metadata.get('was_base64_decoded'):
            lines.append("Note: Content was base64 encoded")
        
        special_elements = metadata.get('special_elements', {})
        if any(special_elements.values()):
            lines.append("\nSpecial elements detected:")
            for key, values in special_elements.items():
                if values:
                    lines.append(f"  - {key}: {len(values)} found")
        
        return "\n".join(lines) if lines else "No additional context"


# Convenience function for quick classification
async def classify_task_quick(task_description: str) -> TaskClassification:
    """
    Quick classification without context
    
    Args:
        task_description: Task to classify
        
    Returns:
        TaskClassification: Classification result
    """
    classifier = TaskClassifier()
    return await classifier.classify_task(task_description)
