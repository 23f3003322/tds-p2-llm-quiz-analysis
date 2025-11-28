"""
Prompt Templates for LLM Operations
Centralized prompt engineering with Pydantic AI support
"""

from typing import Dict, Any, List


class SystemPrompts:
    """System prompts for different agent types"""
    
    ANALYST = """You are an expert data analysis assistant. You understand various data formats, 
can interpret task requirements, and provide structured analysis plans. Always respond accurately 
and follow the specified output format exactly."""
    
    CLASSIFIER = """You are a task classification expert. Analyze task descriptions and determine 
what actions are needed. Be precise and thorough in your analysis. Consider all aspects of the task 
including data sources, processing requirements, and expected outputs.

Classify tasks into appropriate categories and provide confidence levels. Identify key entities 
like URLs, APIs, datasets, and suggest appropriate tools for the task."""
    
    CONTENT_ANALYZER = """You are an expert at analyzing web content and determining how to extract tasks. 
You can identify when content is a direct task description versus when additional actions are needed 
(like downloading files, transcribing audio, visiting other URLs, etc.). 

Be thorough and accurate in your analysis. Consider all special elements like audio files, videos, 
download links, iframes, and images that might contain or lead to the actual task."""
    
    PARAMETER_EXTRACTOR = """You are an expert at extracting structured information from natural language 
task descriptions. Identify all relevant parameters, URLs, filters, and constraints mentioned in the task."""
    
    DECOMPOSER = """You are an expert at breaking down complex tasks into sequential steps. Create clear, 
actionable execution plans that can be followed step-by-step."""


class PromptTemplates:
    """Prompt templates for various operations"""
    
    @staticmethod
    def content_analyzer(
        url: str,
        content_type: str,
        content_preview: str,
        special_elements: Dict[str, List[str]]
    ) -> str:
        """Generate content analyzer prompt"""
        elements_text = PromptTemplates._format_elements(special_elements)
        
        return f"""Analyze this webpage content and determine how to extract the actual task:

URL: {url}
Content Type: {content_type}

Content Preview (first 500 characters):
{content_preview[:500]}

Detected Special Elements:
{elements_text}

Your task:
1. Determine if this content IS the actual task description (ready to use as-is)
2. OR if additional actions are required (download files, transcribe audio, visit links, etc.)

If it's a direct task:
- Set is_direct_task = true
- Extract the task_description
- Explain your reasoning

If it requires actions:
- Set is_direct_task = false
- Identify what needs to be done (download, transcribe, navigate, OCR, etc.)
- List specific URLs that need processing in action_urls
- Explain your reasoning

Be thorough and provide high confidence when you're certain."""
    
    @staticmethod
    def task_classifier(task_description: str) -> str:
        """Generate task classifier prompt"""
        return f"""Analyze this task and provide comprehensive classification:

Task Description:
{task_description}

Classify the task by determining:

1. Primary Task Type (main category):
   - web_scraping: Scraping data from websites
   - api_call: Making API requests  
   - data_cleaning: Cleaning or preprocessing data
   - data_transformation: Reshaping, aggregating, transforming
   - statistical_analysis: Statistical computations
   - ml_analysis: Machine learning tasks
   - text_processing: NLP, text extraction, summarization
   - image_processing: Image analysis, OCR
   - audio_processing: Transcription, audio analysis
   - video_processing: Video analysis
   - geospatial_analysis: Geographic data analysis
   - network_analysis: Graph/network analysis
   - visualization: Creating charts, graphs, maps
   - file_processing: Reading/writing files

2. Secondary Tasks (if any additional steps are involved)

3. Complexity Level:
   - simple: Single straightforward operation
   - medium: Multiple steps or some complexity
   - complex: Many steps, complex logic, or challenging implementation

4. Estimated Steps: How many distinct steps needed (1-20)

5. Requirements:
   - requires_javascript: Does scraping need JavaScript rendering?
   - requires_authentication: Are API keys or auth needed?
   - requires_external_data: Need to fetch data from external sources?

6. Output Format: What should the final output be?
   - text, json, csv, image, chart, html, pdf

7. Key Entities: Extract specific URLs, APIs, datasets, field names mentioned

8. Suggested Tools: Recommend specific libraries/tools for this task
   Examples: playwright, beautifulsoup, pandas, matplotlib, openai, etc.

9. Reasoning: Explain your classification in 1-2 sentences

10. Confidence: How confident are you in this classification? (0.0-1.0)

Be thorough and specific. Consider all aspects of the task."""
    
    @staticmethod
    def parameter_extractor(task_description: str) -> str:
        """Generate parameter extractor prompt"""
        return f"""Extract all specific parameters from this task:

Task:
{task_description}

Extract everything mentioned:
- All URLs mentioned
- Data sources specified
- Filters or conditions
- Output format requirements
- Specific fields/columns to extract
- Time ranges or date constraints
- Numerical limits (top 10, first 5, etc.)
- Any other specific parameters

Be thorough and extract all relevant details."""
    
    @staticmethod
    def task_decomposer(task_description: str, classification: Dict[str, Any]) -> str:
        """Generate task decomposer prompt"""
        import json
        
        return f"""Break down this task into sequential execution steps:

Task Description:
{task_description}

Task Classification:
{json.dumps(classification, indent=2)}

Create a detailed step-by-step execution plan where each step:
- Has a clear, specific action to perform
- Specifies which tool/module to use
- Defines required inputs (and where they come from)
- Defines expected outputs
- Lists dependencies on previous steps (by step number)
- Estimates execution time in seconds

Be detailed and actionable. Each step should be implementable."""
    
    @staticmethod
    def _format_elements(elements: Dict[str, List[str]]) -> str:
        """Format special elements for prompt"""
        if not elements or not any(elements.values()):
            return "None detected"
        
        lines = []
        for key, values in elements.items():
            if values:
                lines.append(f"- {key}: {len(values)} found")
                for i, value in enumerate(values[:2], 1):
                    # Truncate long URLs
                    display_value = value if len(value) <= 80 else value[:77] + "..."
                    lines.append(f"  {i}. {display_value}")
                if len(values) > 2:
                    lines.append(f"  ... and {len(values) - 2} more")
        
        return "\n".join(lines)
