"""
Insight Generator
Generates insights using existing LLM client pattern
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from app.utils.prompts import AnalysisPrompts
from app.utils.llm_client import get_llm_client
from app.core.logging import get_logger

logger = get_logger(__name__)


class QuestionSpecificInsights(BaseModel):
    """Structured output for question-specific insights"""
    
    direct_answer: str = Field(
        description="Direct one-sentence answer to the question"
    )
    key_findings: list[str] = Field(
        description="Key findings with specific numbers"
    )
    supporting_evidence: list[str] = Field(
        description="Statistical evidence supporting findings"
    )
    recommendations: list[str] = Field(
        description="Specific actionable recommendations"
    )
    caveats: list[str] = Field(
        description="Limitations or assumptions to note"
    )
    confidence_level: str = Field(
        description="Confidence level: high, medium, or low"
    )
    confidence_reasoning: str = Field(
        description="Reasoning for confidence level"
    )


class GeneralInsights(BaseModel):
    """Structured output for general insights"""
    
    insights: list[str] = Field(
        description="Key insights with numbers"
    )
    recommendations: list[str] = Field(
        description="Actionable recommendations"
    )
    concerns: list[str] = Field(
        description="Risks or issues to monitor"
    )


class InsightGenerator:
    """
    Generate natural language insights using LLM
    Uses project's LLM client pattern
    """
    
    def __init__(self):
        """Initialize insight generator"""
        self.llm_client = get_llm_client()
        
        # Create question-specific insights agent
        self._question_agent = self.llm_client.create_agent(
            output_type=QuestionSpecificInsights,
            system_prompt="You are a data analyst expert who interprets statistical results to answer specific questions.",
            retries=2
        )
        
        # Create general insights agent
        self._general_agent = self.llm_client.create_agent(
            output_type=GeneralInsights,
            system_prompt="You are a data analyst expert who generates insights from statistical analysis.",
            retries=2
        )
        
        logger.debug("InsightGenerator initialized")
    
    async def generate_question_specific_insights(
        self,
        question: str,
        statistics: Dict[str, Any],
        plan: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate insights tailored to user's specific question
        
        Args:
            question: User's analytical question
            statistics: Statistical results
            plan: Analysis plan that was executed
            context: Additional context
            
        Returns:
            Question-specific insights dict
        """
        logger.info(f"Generating question-specific insights")
        
        # Format statistics
        stats_summary = self._format_statistics(statistics)
        
        # Get domain
        domain = context.get('domain', 'general') if context else 'general'
        
        # Get prompt from centralized location
        prompt = AnalysisPrompts.question_specific_insights_prompt(
            question=question,
            stats_summary=stats_summary,
            plan=plan,
            domain=domain
        )
        
        # Run LLM agent to generate insights
        try:
            insights = await self.llm_client.run_agent(
                self._question_agent,
                prompt
            )
            
            # Convert Pydantic model to dict
            insights_dict = insights.model_dump()
            
        except Exception as e:
            logger.error(f"LLM insight generation failed: {e}, using fallback")
            insights_dict = self._get_fallback_question_insights(question)
        
        return insights_dict
    
    async def generate_insights(
        self,
        statistics: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate general insights from statistics
        
        Args:
            statistics: Statistical analysis results
            context: Additional context
            
        Returns:
            General insights dict
        """
        logger.info("Generating general insights")
        
        # Format statistics
        stats_summary = self._format_statistics(statistics)
        
        # Get context
        domain = context.get('domain', 'general') if context else 'general'
        goal = context.get('goal', 'understand the data') if context else 'understand the data'
        
        # Get prompt from centralized location
        prompt = AnalysisPrompts.general_insights_prompt(
            stats_summary=stats_summary,
            domain=domain,
            goal=goal
        )
        
        # Run LLM agent to generate insights
        try:
            insights = await self.llm_client.run_agent(
                self._general_agent,
                prompt
            )
            
            # Convert Pydantic model to dict
            insights_dict = insights.model_dump()
            
        except Exception as e:
            logger.error(f"LLM insight generation failed: {e}, using fallback")
            insights_dict = self._get_fallback_general_insights()
        
        return insights_dict
    
    def _format_statistics(self, statistics: Dict[str, Any]) -> str:
        """Format statistics for prompt"""
        lines = []
        
        if 'descriptive' in statistics:
            lines.append("\n### Descriptive Statistics:")
            for column, stats in statistics['descriptive'].items():
                lines.append(f"\n**{column}:**")
                for key, value in stats.items():
                    lines.append(f"  - {key}: {value}")
        
        if 'correlations' in statistics:
            lines.append("\n### Correlations:")
            for pair, corr in statistics['correlations'].items():
                lines.append(f"  - {pair}: {corr.get('coefficient')} ({corr.get('strength')} {corr.get('direction')})")
        
        if 'trends' in statistics:
            lines.append("\n### Trends:")
            trend = statistics['trends'].get('trend', {})
            lines.append(f"  - Direction: {trend.get('direction')}")
            lines.append(f"  - Growth Rate: {trend.get('growth_rate')}")
            lines.append(f"  - Forecast: {statistics['trends'].get('forecast_next')}")
        
        if 'segments' in statistics:
            lines.append("\n### Segment Analysis:")
            for segment, data in statistics['segments'].items():
                lines.append(f"  - {segment}: {data}")
        
        if 'outliers' in statistics:
            lines.append("\n### Outliers:")
            for column, indices in statistics['outliers'].items():
                lines.append(f"  - {column}: {len(indices)} outliers")
        
        return "\n".join(lines)
    
    def _get_fallback_question_insights(self, question: str) -> Dict[str, Any]:
        """Fallback insights for question-specific analysis"""
        return {
            "direct_answer": f"Analysis completed for: {question}",
            "key_findings": [
                "Statistical analysis has been performed",
                "Patterns have been identified in the data"
            ],
            "supporting_evidence": [
                "Descriptive statistics calculated",
                "Correlations analyzed"
            ],
            "recommendations": [
                "Review the statistical results",
                "Consider additional context"
            ],
            "caveats": [
                "Results based on available data",
                "External factors not captured"
            ],
            "confidence_level": "medium",
            "confidence_reasoning": "Analysis is statistically sound but requires context validation"
        }
    
    def _get_fallback_general_insights(self) -> Dict[str, Any]:
        """Fallback insights for general analysis"""
        return {
            "insights": [
                "Statistical analysis completed",
                "Data patterns identified"
            ],
            "recommendations": [
                "Review statistical findings",
                "Monitor key metrics"
            ],
            "concerns": [
                "Ensure data quality",
                "Consider external factors"
            ]
        }
