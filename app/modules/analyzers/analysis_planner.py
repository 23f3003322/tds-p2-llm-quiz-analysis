"""
Analysis Planner
LLM determines what analysis to perform based on user question
Uses existing LLM client pattern
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.utils.prompts import AnalysisPrompts
from app.utils.llm_client import get_llm_client
from app.core.logging import get_logger

logger = get_logger(__name__)


class AnalysisPlan(BaseModel):
    """Structured output for analysis plan"""
    
    analysis_types: List[str] = Field(
        description="Types of analysis to perform (descriptive, correlation, trend, etc.)"
    )
    primary_focus: str = Field(
        description="Main aspect to focus on"
    )
    columns_to_analyze: List[str] = Field(
        description="Columns to analyze"
    )
    correlations: List[List[str]] = Field(
        default_factory=list,
        description="Column pairs for correlation analysis"
    )
    segment_by: Optional[str] = Field(
        None,
        description="Column to segment by"
    )
    segment_metric: Optional[str] = Field(
        None,
        description="Metric to compare across segments"
    )
    trend_column: Optional[str] = Field(
        None,
        description="Column for trend analysis"
    )
    value_column: Optional[str] = Field(
        None,
        description="Value to track over time"
    )
    detect_outliers: bool = Field(
        default=False,
        description="Whether to detect outliers"
    )
    outlier_columns: List[str] = Field(
        default_factory=list,
        description="Columns to check for outliers"
    )
    ranking: Optional[Dict[str, Any]] = Field(
        None,
        description="Ranking configuration"
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Filters to apply"
    )
    comparisons: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Comparisons to make"
    )
    reasoning: str = Field(
        description="Why this analysis answers the question"
    )
    expected_insights: List[str] = Field(
        default_factory=list,
        description="Expected insights from analysis"
    )


class AnalysisPlanner:
    """
    Dynamic analysis planner using LLM
    Uses project's LLM client pattern
    """
    
    def __init__(self):
        """Initialize analysis planner"""
        self.llm_client = get_llm_client()
        
        # Create planning agent
        self._planning_agent = self.llm_client.create_agent(
            output_type=AnalysisPlan,
            system_prompt="You are an expert data analyst who plans statistical analysis strategies.",
            retries=2
        )
        
        logger.debug("AnalysisPlanner initialized")
    
    async def plan_analysis(
        self,
        user_question: str,
        data: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create dynamic analysis plan based on user question
        
        Args:
            user_question: User's analytical question
            data: Sample data to understand schema
            context: Additional context (domain, goal, etc.)
            
        Returns:
            Analysis plan dict
        """
        logger.info(f"Planning analysis for: '{user_question}'")
        
        # Infer data schema
        schema = self._infer_schema(data)
        
        # Get data summary
        data_summary = self._get_data_summary(data, schema)
        
        # Format schema for prompt
        schema_text = self._format_schema(schema)
        
        # Build context text
        context_text = ""
        if context:
            domain = context.get('domain', 'general')
            goal = context.get('goal', 'understand the data')
            context_text = f"\nDomain: {domain}\nGoal: {goal}"
        
        # Get prompt from centralized location
        prompt = AnalysisPrompts.analysis_planning_prompt(
            question=user_question,
            schema_text=schema_text,
            summary=data_summary,
            context_text=context_text
        )
        
        # Run LLM agent to generate plan
        try:
            plan = await self.llm_client.run_agent(
                self._planning_agent,
                prompt
            )
            
            # Convert Pydantic model to dict
            plan_dict = plan.model_dump()
            
        except Exception as e:
            logger.error(f"LLM planning failed: {e}, using fallback")
            plan_dict = self._get_fallback_plan()
        
        # Validate and enhance plan
        plan_dict = self._validate_plan(plan_dict, schema)
        
        logger.info(f"✓ Analysis plan created: {plan_dict['analysis_types']}")
        
        return plan_dict
    
    def _infer_schema(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Infer schema from data"""
        if not data:
            return {}
        
        schema = {}
        sample = data[0]
        
        for key, value in sample.items():
            col_info = {
                'name': key,
                'type': 'unknown',
                'sample_value': str(value)[:50]
            }
            
            if isinstance(value, bool):
                col_info['type'] = 'boolean'
            elif isinstance(value, int):
                col_info['type'] = 'integer'
            elif isinstance(value, float):
                col_info['type'] = 'float'
            elif isinstance(value, str):
                try:
                    float(value)
                    col_info['type'] = 'numeric_string'
                except:
                    col_info['type'] = 'text'
            
            schema[key] = col_info
        
        return schema
    
    def _get_data_summary(
        self,
        data: List[Dict[str, Any]],
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get quick data summary"""
        
        summary = {
            'row_count': len(data),
            'column_count': len(schema),
            'numeric_columns': [],
            'text_columns': [],
            'has_temporal_data': False
        }
        
        for col_name, col_info in schema.items():
            if col_info['type'] in ['integer', 'float', 'numeric_string']:
                summary['numeric_columns'].append(col_name)
            elif col_info['type'] == 'text':
                summary['text_columns'].append(col_name)
            
            if any(word in col_name.lower() for word in ['date', 'time', 'month', 'year', 'day']):
                summary['has_temporal_data'] = True
        
        return summary
    
    def _format_schema(self, schema: Dict[str, Any]) -> str:
        """Format schema for prompt"""
        lines = []
        for col_name, col_info in schema.items():
            lines.append(f"  - {col_name}: {col_info['type']} (e.g., {col_info['sample_value']})")
        return "\n".join(lines)
    
    def _get_fallback_plan(self) -> Dict[str, Any]:
        """Fallback plan if LLM fails"""
        return {
            "analysis_types": ["descriptive", "correlation", "segmentation"],
            "primary_focus": "Comprehensive analysis",
            "columns_to_analyze": ["auto_detect_numeric"],
            "correlations": [["auto_detect_all_pairs"]],
            "segment_by": "auto_detect_categorical",
            "segment_metric": "auto_detect_primary_metric",
            "trend_column": None,
            "value_column": None,
            "detect_outliers": True,
            "outlier_columns": ["auto_detect_numeric"],
            "ranking": None,
            "filters": None,
            "comparisons": [],
            "reasoning": "Fallback: Comprehensive statistical analysis",
            "expected_insights": ["Patterns and relationships in data"]
        }
    
    def _validate_plan(
        self,
        plan: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and auto-fill plan"""
        numeric_cols = [k for k, v in schema.items() if v['type'] in ['integer', 'float', 'numeric_string']]
        text_cols = [k for k, v in schema.items() if v['type'] == 'text']
        
        # Auto-detect logic
        if plan.get('columns_to_analyze') == ["auto_detect_numeric"] or not plan.get('columns_to_analyze'):
            plan['columns_to_analyze'] = numeric_cols
        
        if plan.get('correlations') == [["auto_detect_all_pairs"]] or not plan.get('correlations'):
            plan['correlations'] = [
                [numeric_cols[i], numeric_cols[j]]
                for i in range(len(numeric_cols))
                for j in range(i+1, len(numeric_cols))
            ] if len(numeric_cols) >= 2 else []
        
        if plan.get('segment_by') == "auto_detect_categorical" or not plan.get('segment_by'):
            plan['segment_by'] = text_cols[0] if text_cols else None
        
        if plan.get('segment_metric') == "auto_detect_primary_metric" or not plan.get('segment_metric'):
            plan['segment_metric'] = numeric_cols[0] if numeric_cols else None
        
        if plan.get('outlier_columns') == ["auto_detect_numeric"] or not plan.get('outlier_columns'):
            plan['outlier_columns'] = numeric_cols
        
        return plan
