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

class AnalysisPrompts:
    """Prompts for data analysis and insight generation"""
    @staticmethod
    def unified_content_analysis_prompt(
        task_description: str,
        found_urls: List[str],
        current_url: str,
        base_url: str
    ) -> str:
        """Optimized unified analysis prompt"""
        urls_text = "\n".join(f"- {url}" for url in found_urls) if found_urls else "None"
        
        return f"""Analyze this quiz/task content and extract all critical information.

    **Current URL:** {current_url}
    **Base URL:** {base_url}

    **Content:**
    {task_description}

    **URLs found:**
    {urls_text}

    ---

    ## EXTRACT:

    ### 1. SUBMISSION URL (Priority #1)
    Where to POST the final answer.

    **Search for:** "POST to", "submit to", "send to", "answer to"
    **Extract from:** Text, markdown links `[text](URL)`, relative paths `/submit`
    **Set submission_url_is_relative=True** if starts with `/`

    ### 2. REDIRECT DETECTION
    **is_redirect=True** if content says "visit URL" or "task at URL" (directs elsewhere)
    **is_redirect=False** if content IS the task (has instructions)

    Provide **question_url** if redirect detected.

    ### 3. INSTRUCTION PARSING
    Break into steps (ONLY if is_redirect=False).

    **Actions:** scrape, extract, calculate, submit, download, transcribe, analyze, visit
    **Each step:** step_number, action, description, target, dependencies

    ### 4. ASSESSMENT
    - **overall_goal**: One sentence
    - **complexity**: trivial/simple/moderate/complex  
    - **confidence**: 0.0-1.0

    ---

    ## EXAMPLE:

    **Input:**
    "Scrape /data?email=... Get the secret code. POST code to [/submit](https://example.com/submit)"

    **Output:**
    {{
    "is_redirect": false,
    "question_url": null,
    "redirect_reasoning": "Contains task instructions",
    "submission_url": "/submit",
    "submission_url_is_relative": true,
    "submission_reasoning": "Found 'POST code to /submit'",
    "instructions": [
    {{"step_number": 1, "action": "scrape", "description": "Scrape /data page", "target": "/data?email=...", "dependencies": []}},
    {{"step_number": 2, "action": "extract", "description": "Extract secret code", "target": "secret code", "dependencies": }},
    {{"step_number": 3, "action": "submit", "description": "POST code to /submit", "target": "/submit", "dependencies": }}
    ],
    "overall_goal": "Scrape, extract, and submit secret code",
    "complexity": "simple",
    "confidence": 0.92
    }}

    text

    Now analyze the content above."""

    @staticmethod
    def question_analysis_prompt(
        instructions: List[str],
        difficulty: int,
        is_personalized: bool,
        title: str,
        heading: str,
        base_url: str,
        user_email: str,
        available_files: List[Dict[str, Any]]
    ) -> str:
            """
            Generate prompt for analyzing question.
            Focused on extracting what's needed to generate the answer.
            """
            
            files_text = "\n".join(
                f"- {f.get('filename', 'unknown')} ({f.get('type', 'unknown')})"
                for f in available_files
            ) if available_files else "None"
            
            instructions_text = "\n".join(
                f"{i+1}. {inst}" 
                for i, inst in enumerate(instructions)
            )
            
            return f"""Analyze this technical quiz question to determine how to generate the correct answer.

    # QUESTION METADATA
    - **Title**: {title}
    - **Heading**: {heading}
    - **Difficulty**: {difficulty}/5 (1=easiest, 5=hardest)
    - **Personalized**: {is_personalized}
    - **Base URL**: {base_url}
    - **User Email**: {user_email}

    # INSTRUCTIONS
    {instructions_text}

    # AVAILABLE FILES
    {files_text}

    ---

    # YOUR ANALYSIS TASK

    Extract the following information to enable answer generation:

    ## 1. QUESTION TYPE
    Categorize the task:
    - **cli_command**: Generate command strings (uv, git, curl, docker)
    - **file_path**: Return file paths or URLs
    - **data_processing**: Process CSV/JSON/ZIP files
    - **image_analysis**: Analyze images (colors, pixels, differences)
    - **audio_transcription**: Transcribe audio to text
    - **api_interaction**: Make API calls (GitHub, REST APIs)
    - **document_parsing**: Extract data from PDFs
    - **calculation**: Mathematical computations (sums, F1 scores)
    - **text_generation**: Generate YAML, prompts, configuration
    - **optimization**: Solve constraint/optimization problems
    - **llm_reasoning**: Multi-step reasoning or tool planning

    ## 2. ANSWER FORMAT
    How should the final answer be formatted?
    - **plain_string**: Raw text, no quotes, no JSON (e.g., "uv http get ...")
    - **json_object**: JSON dictionary (e.g., {{"key": "value"}})
    - **json_array**: JSON list (e.g., ["a", "b", "c"])
    - **number**: Integer or float (e.g., 42 or 3.14)
    - **single_letter**: One character (e.g., A, B, or C)

    ## 3. KEY COMPONENTS
    Extract specific data needed to generate the answer:

    **For cli_command:**
    - tool: "uv", "git", "curl"
    - subcommand: "http get", "add", "commit"
    - url_template: Pattern with placeholders
    - flags: ["-H", "-m", "-p"]
    - arguments: Headers, messages, parameters

    **For file_path:**
    - path: Exact path or pattern

    **For data_processing:**
    - operations: ["normalize", "filter", "aggregate"]
    - output_format: "json", "csv"
    - sorting: Field and direction

    **For calculations:**
    - formula: Mathematical expression
    - input_sources: Where data comes from
    - precision: Decimal places

    **For any type:**
    - Any other relevant details from instructions

    ## 4. PERSONALIZATION
    Determine if answer depends on user's email:

    **Types:**
    - **email_in_url**: Email appears in URL (e.g., ?email={{user_email}})
    - **email_length_offset**: offset = len(email) mod N, add to result
    - **email_length_conditional**: Different answer based on email length (even/odd)

    **Details:**
    - Which mod value? (mod 2, mod 3, mod 5)
    - How to apply? (add to result, choose option)

    ## 5. FILE REQUIREMENTS
    Does the question need files from available_files list?
    - Which file types? (csv, json, png, pdf, opus, zip)
    - What to do with them? (process, analyze, extract)

    ## 6. EXTERNAL RESOURCES
    Does the question require fetching from another URL/endpoint?
    - API endpoints mentioned in instructions
    - Data sources not in available_files
    - Example: "Use GitHub API with params in /project2/gh-tree.json"

    ## 7. CRITICAL CONSTRAINTS
    Extract must-follow rules:
    - "command string" not "command output"
    - Exact decimal places (2, 4)
    - Sorting order (ascending, descending)
    - Case sensitivity (lowercase, uppercase)
    - Separators (comma, space, newline)
    - Quote style ("double", 'single', none)
    - No markdown formatting
    - Specific value ranges

    ## 8. SUBMISSION URL PATH
    The URL path for THIS specific question (from title/heading).
    Pattern: /project2-{{question-name}}
    Example: /project2-uv, /project2-git, /project2-md

    ---

    # EXAMPLES

    ## Example 1: CLI Command (Q2-like)

    **Instructions:**
    1. Craft the command string using uv http get on {{{{base_url}}}}/project2/uv.json?email=<your email>
    2. Include header Accept: application/json
    3. POST that exact command string as answer

    **Analysis:**
    {{
"question_type": "cli_command",
"answer_format": "plain_string",
"key_components": {{
"tool": "uv",
"subcommand": "http get",
"url_template": "{{{{base_url}}}}/project2/uv.json?email={{{{user_email}}}}",
"headers": [{{"name": "Accept", "value": "application/json"}}],
"header_flag": "-H"
}},
"requires_personalization": true,
"personalization_type": "email_in_url",
"personalization_details": "User email in URL query parameter",
"requires_files": false,
"required_file_types": [],
"requires_external_fetch": false,
"external_resources": [],
"critical_constraints": [
"Return command string only, not output",
"Use double quotes for header value",
"Format: tool subcommand url -H \"header: value\""
],
"submission_url_path": "/project2-uv",
"reasoning": "Instructions explicitly ask for 'command string' using specific tool and parameters",
"confidence": 0.98
}}

text

## Example 2: File Path (Q4-like)

**Instructions:**
1. The correct relative link target is exactly /project2/data-preparation.md
2. Submit that exact string. Do not wrap in Markdown/HTML

**Analysis:**
{{
"question_type": "file_path",
"answer_format": "plain_string",
"key_components": {{
"path": "/project2/data-preparation.md"
}},
"requires_personalization": false,
"requires_files": false,
"requires_external_fetch": false,
"critical_constraints": [
"Exact string: /project2/data-preparation.md",
"No markdown formatting",
"No HTML tags",
"No quotes"
],
"submission_url_path": "/project2-md",
"reasoning": "Instructions provide exact path to return",
"confidence": 1.0
}}

text

## Example 3: Data Processing with Personalization (Q9-like)

**Instructions:**
1. Download logs.zip and sum bytes where event=="download"
2. Compute offset = (length of your email) mod 5
3. Final answer = base sum + offset

**Available Files:**
- logs.zip (zip)

**Analysis:**
{{
"question_type": "data_processing",
"answer_format": "number",
"key_components": {{
"file": "logs.zip",
"operation": "sum",
"field": "bytes",
"filter": {{"event": "download"}},
"offset_formula": "len(user_email) mod 5"
}},
"requires_personalization": true,
"personalization_type": "email_length_offset",
"personalization_details": "Add (len(email) mod 5) to base sum",
"requires_files": true,
"required_file_types": ["zip"],
"requires_external_fetch": false,
"critical_constraints": [
"Filter: event == 'download'",
"Sum the bytes field",
"Add email length offset",
"Return integer only"
],
"submission_url_path": "/project2-logs",
"reasoning": "File processing with email-based offset calculation",
"confidence": 0.92
}}

text

---

# NOW ANALYZE

Analyze the question above and return a complete QuestionAnalysis object.
Be precise and extract ALL relevant details from the instructions.
"""

    @staticmethod
    def analysis_planning_prompt(
        question: str,
        schema_text: str,
        summary: Dict[str, Any],
        context_text: str = ""
    ) -> str:
        """
        Prompt for LLM to plan analysis strategy
        
        Args:
            question: User's analytical question
            schema_text: Formatted data schema
            summary: Data summary statistics
            context_text: Optional context (domain, goal)
            
        Returns:
            Prompt string
        """
        return f"""You are an expert data analyst. A user has a question about their data, and you need to determine what statistical analysis will best answer it.

User Question: "{question}"{context_text}

Available Data:
- Total Rows: {summary['row_count']}
- Columns: {summary['column_count']}

Column Schema:
{schema_text}

Numeric Columns: {', '.join(summary['numeric_columns']) if summary['numeric_columns'] else 'None'}
Text/Categorical Columns: {', '.join(summary['text_columns']) if summary['text_columns'] else 'None'}
Has Temporal Data: {summary['has_temporal_data']}

Based on this question and data, create a comprehensive analysis plan.

Available Analysis Types:
1. **descriptive**: Calculate mean, median, std, min, max for numeric columns
2. **correlation**: Find relationships between numeric variables
3. **trend**: Detect patterns over time (if temporal data exists)
4. **segmentation**: Compare groups using categorical columns
5. **distribution**: Analyze data spread, skewness, outliers
6. **ranking**: Identify top/bottom performers
7. **comparison**: Compare specific groups or time periods

Create a JSON analysis plan:

{{
  "analysis_types": ["descriptive", "correlation", ...],
  "primary_focus": "What aspect to focus on",
  "columns_to_analyze": ["col1", "col2", ...],
  "correlations": [
    ["col1", "col2"],
    ["col3", "col4"]
  ],
  "segment_by": "category_column_name" or null,
  "segment_metric": "metric_to_compare" or null,
  "trend_column": "temporal_column" or null,
  "value_column": "what_to_track_over_time" or null,
  "detect_outliers": true or false,
  "outlier_columns": ["col1", "col2"],
  "ranking": {{
    "column": "column_to_rank",
    "by": "metric_to_rank_by",
    "top_n": 5,
    "ascending": false
  }} or null,
  "filters": {{
    "column": "value"
  }} or null,
  "comparisons": [
    {{"type": "group", "column": "category", "values": ["A", "B"]}}
  ] or [],
  "reasoning": "Explain why this analysis answers the user's question",
  "expected_insights": ["What insights might we find", "What patterns to look for"]
}}

Important:
- Choose analyses that DIRECTLY answer the user's question
- Use actual column names from the schema
- Be specific about what to compare, correlate, or segment
- If question asks "why", include correlation and segmentation
- If question asks "what", include ranking and descriptive stats
- If question asks "when" or "trend", include temporal analysis

Return ONLY valid JSON, no additional text.
"""
    @staticmethod
    def question_specific_insights_prompt(
        question: str,
        stats_summary: str,
        plan: Dict[str, Any],
        domain: str = "general"
    ) -> str:
        """
        Prompt for generating question-specific insights
        
        Args:
            question: User's original question
            stats_summary: Formatted statistical results
            plan: Analysis plan that was executed
            domain: Domain context
            
        Returns:
            Prompt string
        """
        return f"""You are a data analyst expert. A user asked a specific question about their data, 
and statistical analysis has been performed. Interpret the results to directly answer their question.

User's Original Question: "{question}"

Domain: {domain}

Analysis Performed:
- Focus: {plan.get('primary_focus', 'Comprehensive analysis')}
- Methods: {', '.join(plan.get('analysis_types', []))}

Statistical Results:
{stats_summary}

Your task: Provide a clear, actionable answer to the user's question based on these statistics.

Generate a JSON response with:

{{
  "direct_answer": "One clear sentence directly answering the question",
  "key_findings": [
    "Finding 1 with specific numbers",
    "Finding 2 with specific numbers",
    "Finding 3 with specific numbers"
  ],
  "supporting_evidence": [
    "Statistical evidence 1",
    "Statistical evidence 2"
  ],
  "recommendations": [
    "Specific action 1 based on findings",
    "Specific action 2 based on findings",
    "Specific action 3 based on findings"
  ],
  "caveats": [
    "Limitation or assumption to note",
    "What to validate or investigate further"
  ],
  "confidence_level": "high/medium/low",
  "confidence_reasoning": "Why you have this confidence level"
}}

Rules:
- ALWAYS reference actual numbers from the statistics
- Be specific, not generic
- Connect findings directly to the original question
- Prioritize actionable insights
- If data doesn't fully answer the question, say so

Return ONLY valid JSON.
"""
    
    @staticmethod
    def general_insights_prompt(
        stats_summary: str,
        domain: str = "general",
        goal: str = "understand the data"
    ) -> str:
        """
        Prompt for generating general insights
        
        Args:
            stats_summary: Formatted statistical results
            domain: Domain context
            goal: Analysis goal
            
        Returns:
            Prompt string
        """
        return f"""You are a data analyst expert. Analyze statistical results and provide insights.

Domain: {domain}
Goal: {goal}

Statistical Analysis:
{stats_summary}

Based on this analysis, provide:

1. **Key Insights** (3-5 bullet points):
   - What are the most important findings?
   - What patterns or relationships stand out?
   - What is surprising or noteworthy?

2. **Recommendations** (3-5 actionable items):
   - What actions should be taken based on these findings?
   - How can these insights be leveraged?
   - What should be prioritized?

3. **Concerns or Risks** (2-3 points):
   - What potential issues should be monitored?
   - What assumptions should be validated?
   - What limitations exist in the data?

Be specific, actionable, and data-driven. Reference actual numbers from the statistics.

Generate JSON:

{{
  "insights": [
    "Key insight 1 with numbers",
    "Key insight 2 with numbers",
    "Key insight 3 with numbers"
  ],
  "recommendations": [
    "Action 1",
    "Action 2",
    "Action 3"
  ],
  "concerns": [
    "Risk or issue 1",
    "Risk or issue 2"
  ]
}}

Return ONLY valid JSON.
"""

class ReportPrompts:
    """Prompts for report generation"""
    
    @staticmethod
    def answer_generation_prompt(
        question: str,
        statistics: str,
        insights: str,
        has_chart: bool,
        format_type: str = "text"
    ) -> str:
        """
        Prompt for generating final quiz answer
        
        Args:
            question: Original quiz question
            statistics: Statistical results
            insights: Analysis insights
            has_chart: Whether a chart is included
            format_type: Output format
            
        Returns:
            Prompt string
        """
        
        chart_text = ""
        if has_chart:
            chart_text = "\n\nNote: A chart has been generated and will be embedded in the answer."
        
        return f"""You are answering a quiz question. Generate a clear, complete, and well-structured answer.

Quiz Question: "{question}"

Statistical Results:
{statistics}

Analysis Insights:
{insights}{chart_text}

Your task: Generate a comprehensive answer that:

1. **Directly answers the question** in the first sentence
2. **Provides supporting evidence** from the statistics
3. **Includes key insights** and findings
4. **Gives actionable recommendations** if applicable
5. **Is well-organized** and easy to read

Format: {format_type}

Requirements:
- Start with a direct answer (1-2 sentences)
- Use bullet points for clarity
- Reference specific numbers from statistics
- Be concise but complete
- Professional tone
- No speculation - only data-driven conclusions

Generate the answer now:
"""


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

    @staticmethod
    def url_detection_prompt(
        content: str,
        urls: list,
        request_url: str
    ) -> str:
        """
        Prompt for detecting Question URL from content
        
        Args:
            content: Fetched content
            urls: List of URLs found in content
            request_url: Original request URL
            
        Returns:
            Formatted prompt
        """
        urls_text = "\n".join(f"{i+1}. {url}" for i, url in enumerate(urls)) if urls else "None"
        
        return f"""You are analyzing content from a TDS quiz/task system to determine URL relationships.

    **Context:**
    - We fetched content from: {request_url}
    - This content might either:
    1. BE the actual task/question (return is_redirect=False)
    2. REDIRECT/POINT to another URL where the actual task is located (return is_redirect=True)

    **URLs found in content:**
    {urls_text}

    **Content (truncated to 1500 chars):**
    {content[:1500]}

    **Your Task:**
    Analyze if this content IS the actual task, or if it REDIRECTS to another URL to get the task.

    **URL Type Definitions:**
    - **question_url**: URL to visit to GET the actual task/question
    - **data_url**: URL to GET/SCRAPE data from (as part of task instructions)
    - **submission_url**: URL to POST the final answer to
    - **reference_url**: URL for reference/documentation only

    **Decision Rules:**

    1. **is_redirect=True** when:
    - Content explicitly says "visit <url>", "your task is at <url>", "go to <url>"
    - Content is very short (< 100 chars) with just a URL
    - Content describes WHERE to find the task, not WHAT the task is
    - Primary purpose is to direct you to another location

    2. **is_redirect=False** when:
    - Content contains actual task instructions (scrape, analyze, calculate, etc.)
    - URLs are mentioned as DATA SOURCES or SUBMISSION endpoints
    - Content is the task itself, even if it references other URLs

    **Examples:**

    Example 1 (REDIRECT):
    Content: "Your quiz is available at https://example.com/quiz-834"
    → is_redirect=True, question_url="https://example.com/quiz-834"
    → Reasoning: Content tells you WHERE to go, not WHAT to do

    Example 2 (ACTUAL TASK):
    Content: "Scrape https://example.com/data and extract the top 5 prices. Submit to https://example.com/submit"
    → is_redirect=False
    → Reasoning: This IS the task. URLs are for data source and submission, not for getting the task

    Example 3 (REDIRECT with multiple URLs):
    Content: "Visit https://example.com/quiz-834 to receive your assignment. You'll be asked to scrape another website."
    → is_redirect=True, question_url="https://example.com/quiz-834"
    → Reasoning: Content directs you to quiz-834 to GET the actual task

    Example 4 (ACTUAL TASK with multiple URLs):
    Content: "Download data from https://api.example.com/data and compare with https://example.com/reference. Calculate the difference."
    → is_redirect=False
    → Reasoning: This IS the task. Both URLs are data sources for completing the task

    Example 5 (SHORT REDIRECT):
    Content: "https://example.com/quiz-834"
    → is_redirect=True, question_url="https://example.com/quiz-834"
    → Reasoning: Only a URL, no task instructions

    **Now analyze the content above and provide your analysis.**"""
   