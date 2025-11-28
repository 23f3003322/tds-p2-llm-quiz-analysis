"""
Parameter Extractor
Extracts structured parameters from task descriptions using LLM
"""

from typing import Dict, Any, Optional, List
import re
from urllib.parse import urlparse

from app.orchestrator.parameter_models import (
    ExtractedParameters,
    ParameterExtractionResult,
    DataSource,
    URLParameter
)
from app.utils.llm_client import get_llm_client
from app.utils.prompts import SystemPrompts, PromptTemplates
from app.core.logging import get_logger
from app.core.exceptions import TaskProcessingError

logger = get_logger(__name__)


class ParameterExtractor:
    """
    Extracts structured parameters from task descriptions
    Uses LLM with Pydantic validation for robust extraction
    """
    
    def __init__(self):
        """Initialize parameter extractor"""
        self.llm_client = get_llm_client()
        
        # Create parameter extraction agent
        self._extraction_agent = self.llm_client.create_agent(
            output_type=ExtractedParameters,
            system_prompt=SystemPrompts.PARAMETER_EXTRACTOR,
            retries=2
        )
        
        logger.debug("ParameterExtractor initialized")
    
    async def extract_parameters(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ParameterExtractionResult:
        """
        Extract parameters from task description
        
        Args:
            task_description: The task description to analyze
            context: Optional context (classification, metadata, etc.)
            
        Returns:
            ParameterExtractionResult: Extracted parameters with metadata
        """
        logger.info("🔍 Extracting parameters from task")
        logger.debug(f"Task length: {len(task_description)} chars")
        
        try:
            # First, try quick rule-based extraction for simple cases
            quick_params = self._quick_extract(task_description)
            
            # Then use LLM for comprehensive extraction
            prompt = PromptTemplates.parameter_extractor(
                task_description=task_description,
                context=context or {},
                quick_extraction=quick_params
            )
            
            logger.debug(f"Parameter extraction prompt: {len(prompt)} chars")
            
            # Run extraction agent
            parameters = await self.llm_client.run_agent(
                self._extraction_agent,
                prompt
            )
            
            # Validate and enrich parameters
            parameters = self._validate_and_enrich(parameters, task_description)
            
            logger.info(
                f"✅ Parameters extracted | "
                f"Sources: {len(parameters.data_sources)} | "
                f"URLs: {len(parameters.urls)} | "
                f"Filters: {len(parameters.filters)} | "
                f"Confidence: {parameters.confidence:.2f}"
            )
            
            return ParameterExtractionResult(
                parameters=parameters,
                raw_task=task_description,
                extraction_method='hybrid',  # Rule-based + LLM
                success=True,
                errors=[]
            )
            
        except Exception as e:
            logger.error(f"❌ Parameter extraction failed: {str(e)}", exc_info=True)
            
            # Fallback to rule-based extraction
            try:
                fallback_params = self._fallback_extraction(task_description)
                
                return ParameterExtractionResult(
                    parameters=fallback_params,
                    raw_task=task_description,
                    extraction_method='rule_based',
                    success=True,
                    errors=[f"LLM extraction failed, used fallback: {str(e)}"]
                )
            except Exception as fallback_error:
                logger.error(f"❌ Fallback extraction failed: {fallback_error}")
                
                return ParameterExtractionResult(
                    parameters=ExtractedParameters(),
                    raw_task=task_description,
                    extraction_method='rule_based',
                    success=False,
                    errors=[str(e), str(fallback_error)]
                )
    
    def _quick_extract(self, task: str) -> Dict[str, Any]:
        """
        Quick rule-based extraction for common patterns
        Used to guide LLM and as fallback
        """
        result = {
            'urls': [],
            'numbers': [],
            'dates': [],
            'keywords': []
        }
        
        # Extract URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        result['urls'] = re.findall(url_pattern, task)
        
        # Extract numbers
        number_pattern = r'\b\d+(?:\.\d+)?\b'
        result['numbers'] = [float(n) for n in re.findall(number_pattern, task)]
        
        # Extract potential date patterns
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}'  # DD Month YYYY
        ]
        for pattern in date_patterns:
            result['dates'].extend(re.findall(pattern, task, re.IGNORECASE))
        
        # Extract common keywords
        keywords = [
            'filter', 'sort', 'group', 'aggregate', 'sum', 'average', 'count',
            'top', 'bottom', 'limit', 'where', 'visualize', 'plot', 'chart',
            'download', 'scrape', 'extract', 'analyze', 'compare'
        ]
        result['keywords'] = [kw for kw in keywords if kw in task.lower()]
        
        return result
    
    def _validate_and_enrich(
        self,
        parameters: ExtractedParameters,
        task: str
    ) -> ExtractedParameters:
        """
        Validate extracted parameters and add missing information
        """
        # Ensure all URLs are properly formatted
        for url_param in parameters.urls:
            if not url_param.url.startswith(('http://', 'https://')):
                url_param.url = 'https://' + url_param.url
        
        # Calculate complexity score if not set
        if parameters.complexity_score == 0.0:
            complexity = 0.0
            complexity += len(parameters.data_sources) * 0.1
            complexity += len(parameters.filters) * 0.05
            complexity += len(parameters.aggregations) * 0.1
            complexity += len(parameters.visualizations) * 0.1
            complexity += 0.3 if parameters.urls else 0.0
            
            parameters.complexity_score = min(1.0, complexity)
        
        # Estimate execution time if not set
        if parameters.estimated_execution_time == 60:
            base_time = 30
            base_time += len(parameters.data_sources) * 10
            base_time += len(parameters.urls) * 20
            base_time += len(parameters.filters) * 2
            base_time += len(parameters.visualizations) * 15
            
            parameters.estimated_execution_time = base_time
        
        # Set confidence if not set
        if parameters.confidence == 0.0:
            # Base confidence on how much was extracted
            extracted_count = (
                len(parameters.data_sources) +
                len(parameters.urls) +
                len(parameters.filters) +
                len(parameters.columns)
            )
            
            if extracted_count > 0:
                parameters.confidence = min(0.95, 0.5 + extracted_count * 0.1)
            else:
                parameters.confidence = 0.3
        
        return parameters
    
    def _fallback_extraction(self, task: str) -> ExtractedParameters:
        """
        Fallback rule-based extraction when LLM fails
        """
        logger.info("Using fallback rule-based extraction")
        
        quick_extract = self._quick_extract(task)
        
        parameters = ExtractedParameters()
        
        # Extract URLs as data sources
        for url in quick_extract['urls']:
            parameters.urls.append(URLParameter(
                url=url,
                purpose="Detected URL (purpose unknown)",
                requires_javascript=False,
                requires_authentication=False
            ))
            
            parameters.data_sources.append(DataSource(
                type='url',
                location=url,
                format=self._guess_format_from_url(url),
                description=f"Data source from {url}"
            ))
        
        # Add notes
        parameters.notes.append("Extracted using fallback rule-based method")
        parameters.notes.append("Some parameters may be missing or inaccurate")
        
        # Set low confidence
        parameters.confidence = 0.3
        parameters.complexity_score = 0.5
        
        return parameters
    
    def _guess_format_from_url(self, url: str) -> Optional[str]:
        """Guess data format from URL"""
        url_lower = url.lower()
        
        if url_lower.endswith('.csv'):
            return 'csv'
        elif url_lower.endswith('.json'):
            return 'json'
        elif url_lower.endswith('.xml'):
            return 'xml'
        elif url_lower.endswith(('.xlsx', '.xls')):
            return 'excel'
        elif 'api' in url_lower:
            return 'api'
        
        return None


# Convenience function
async def extract_parameters_quick(task_description: str) -> ExtractedParameters:
    """
    Quick parameter extraction without context
    
    Args:
        task_description: Task to extract parameters from
        
    Returns:
        ExtractedParameters: Extracted parameters
    """
    extractor = ParameterExtractor()
    result = await extractor.extract_parameters(task_description)
    return result.parameters
    