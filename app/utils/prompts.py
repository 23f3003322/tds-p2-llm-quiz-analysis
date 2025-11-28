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


    PARAMETER_EXTRACTOR = """You are a parameter extraction expert. 
Your job is to analyze task descriptions and extract ALL relevant parameters in a structured format.

Extract:
1. **Data Sources**: URLs, files, APIs, databases mentioned
2. **Filters**: Conditions to apply (equals, greater than, contains, etc.)
3. **Columns/Fields**: Specific columns or fields to extract or use
4. **Time Ranges**: Date/time filters (absolute or relative)
5. **Numerical Constraints**: Limits, thresholds, top N, ranges
6. **Geographic Filters**: Country, city, region, coordinates
7. **Aggregations**: Sum, average, count, group by operations
8. **Sorting**: Sort order specifications
9. **Visualizations**: Charts, graphs, maps required
10. **Output Format**: CSV, JSON, Excel, PDF, etc.

Be precise and thorough. If something is ambiguous, make reasonable assumptions based on context.
Extract EVERYTHING that could be useful for task execution."""


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
    def parameter_extractor(
        task_description: str,
        context: Dict[str, Any],
        quick_extraction: Dict[str, Any]
    ) -> str:
        """Generate parameter extraction prompt"""
        
        prompt_parts = [
            "Extract ALL parameters from this task description:\n",
            f"TASK:\n{task_description}\n"
        ]
        
        # Add context if available
        if context:
            prompt_parts.append(f"\nCONTEXT:\n")
            
            if 'classification' in context:
                classification = context['classification']
                prompt_parts.append(
                    f"- Task Type: {classification.get('primary_task', 'unknown')}\n"
                )
                prompt_parts.append(
                    f"- Complexity: {classification.get('complexity', 'unknown')}\n"
                )
            
            if 'metadata' in context:
                prompt_parts.append(f"- Metadata: {context['metadata']}\n")
        
        # Add quick extraction hints
        if quick_extraction:
            prompt_parts.append(f"\nQUICK ANALYSIS:\n")
            
            if quick_extraction.get('urls'):
                prompt_parts.append(f"- URLs found: {len(quick_extraction['urls'])}\n")
            
            if quick_extraction.get('numbers'):
                prompt_parts.append(
                    f"- Numbers found: {quick_extraction['numbers'][:5]}\n"
                )
            
            if quick_extraction.get('dates'):
                prompt_parts.append(f"- Dates found: {quick_extraction['dates']}\n")
            
            if quick_extraction.get('keywords'):
                prompt_parts.append(
                    f"- Keywords: {', '.join(quick_extraction['keywords'])}\n"
                )
        
        prompt_parts.append("""
INSTRUCTIONS:
1. Identify ALL data sources (URLs, files, APIs)
2. Extract ALL filters and conditions
3. List ALL columns/fields mentioned
4. Extract time ranges (if any)
5. Extract numerical constraints (limits, top N, thresholds)
6. Identify geographic filters (if any)
7. Extract aggregation operations (sum, average, count, group by)
8. Identify sorting requirements
9. Extract visualization requirements (charts, graphs, maps)
10. Determine output format

Be thorough and precise. Extract everything that could help execute this task.
""")
        
        return ''.join(prompt_parts)
    
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
