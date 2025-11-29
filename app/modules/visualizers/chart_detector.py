"""
Chart Detector
Determines if a question requires a chart
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from app.utils.llm_client import get_llm_client
from app.core.logging import get_logger

logger = get_logger(__name__)


class ChartRequirement(BaseModel):
    """Structured output for chart requirement"""
    
    requires_chart: bool = Field(
        description="Whether the question explicitly asks for a chart/graph/plot"
    )
    chart_type: Optional[str] = Field(
        None,
        description="Type of chart: bar, line, pie, scatter, histogram, heatmap, box"
    )
    x_axis: Optional[str] = Field(
        None,
        description="What to show on X axis"
    )
    y_axis: Optional[str] = Field(
        None,
        description="What to show on Y axis"
    )
    title: Optional[str] = Field(
        None,
        description="Suggested chart title"
    )
    reasoning: str = Field(
        description="Why this chart type is appropriate"
    )


class ChartDetector:
    """
    Detects if a question requires visualization
    Uses LLM to understand intent
    """
    
    def __init__(self):
        """Initialize chart detector"""
        self.llm_client = get_llm_client()
        
        # Create detection agent
        self._detection_agent = self.llm_client.create_agent(
            output_type=ChartRequirement,
            system_prompt="You detect if a question explicitly asks for a chart or visualization.",
            retries=2
        )
        
        logger.debug("ChartDetector initialized")
    
    async def detect_chart_requirement(
        self,
        question: str,
        data_summary: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect if question asks for a chart
        
        Args:
            question: User's question
            data_summary: Summary of available data
            
        Returns:
            Chart requirement dict
        """
        logger.info(f"Detecting chart requirement for: '{question}'")
        
        # Build prompt
        prompt = self._build_detection_prompt(question, data_summary)
        
        # Run LLM detection
        try:
            requirement = await self.llm_client.run_agent(
                self._detection_agent,
                prompt
            )
            
            result = requirement.model_dump()
            
        except Exception as e:
            logger.error(f"Chart detection failed: {e}")
            result = {
                "requires_chart": self._fallback_detection(question),
                "chart_type": None,
                "x_axis": None,
                "y_axis": None,
                "title": None,
                "reasoning": "Fallback detection"
            }
        
        logger.info(f"Chart required: {result['requires_chart']}")
        
        return result
    
    def _build_detection_prompt(
        self,
        question: str,
        data_summary: Optional[Dict[str, Any]]
    ) -> str:
        """Build prompt for chart detection"""
        
        data_text = ""
        if data_summary:
            data_text = f"\n\nAvailable data:\n- Columns: {', '.join(data_summary.get('columns', []))}\n- Rows: {data_summary.get('rows', 0)}"
        
        return f"""Analyze this question and determine if it explicitly asks for a chart or visualization.

Question: "{question}"{data_text}

Important rules:
- ONLY return requires_chart=true if the question EXPLICITLY uses words like:
  "chart", "graph", "plot", "visualize", "show graphically", "create a chart"
- If the question just asks for analysis without mentioning visualization, return false
- Examples:
  ✓ "Create a bar chart of sales by category" → requires_chart=true
  ✓ "Plot the trend over time" → requires_chart=true
  ✗ "What are the top products?" → requires_chart=false
  ✗ "Analyze sales performance" → requires_chart=false

If a chart IS required, determine:
- chart_type: bar, line, pie, scatter, histogram, heatmap, box
- x_axis: What variable goes on X axis
- y_axis: What variable goes on Y axis
- title: Descriptive chart title

Be conservative - only require charts when explicitly asked!
"""
    
    def _fallback_detection(self, question: str) -> bool:
        """Fallback keyword-based detection"""
        
        chart_keywords = [
            'chart', 'graph', 'plot', 'visualize', 'visualization',
            'bar chart', 'line chart', 'pie chart', 'scatter plot',
            'histogram', 'heatmap', 'show graphically'
        ]
        
        question_lower = question.lower()
        
        return any(keyword in question_lower for keyword in chart_keywords)
