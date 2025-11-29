"""
Report Generator
Generates final quiz answers from all previous steps
"""

from typing import Dict, Any, Optional
import time
from pydantic import BaseModel, Field

from app.modules.generators.base_generator import BaseGenerator, ReportResult, OutputFormat
from app.modules.generators.answer_formatter import AnswerFormatter
from app.utils.prompts import ReportPrompts
from app.utils.llm_client import get_llm_client
from app.modules.base import ModuleCapability, ModuleResult
from app.modules.capabilities import OutputCapability
from app.core.logging import get_logger

logger = get_logger(__name__)


class QuizAnswer(BaseModel):
    """Structured output for quiz answer"""
    
    direct_answer: str = Field(
        description="Direct answer to the question (1-2 sentences)"
    )
    key_findings: list[str] = Field(
        description="Key findings with specific numbers (3-5 points)"
    )
    supporting_evidence: list[str] = Field(
        default_factory=list,
        description="Statistical evidence supporting the answer"
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Actionable recommendations based on findings"
    )


class ReportGenerator(BaseGenerator):
    """
    Report generator for quiz answers
    Compiles all outputs into final answer
    """
    
    def __init__(self):
        super().__init__(name="report_generator")
        self.llm_client = get_llm_client()
        self.formatter = AnswerFormatter()
        
        # Create answer generation agent
        self._answer_agent = self.llm_client.create_agent(
            output_type=QuizAnswer,
            system_prompt="You generate clear, concise, data-driven answers to quiz questions.",
            retries=2
        )
        
        logger.debug("ReportGenerator initialized")
    
    def get_capabilities(self) -> ModuleCapability:
        """Get module capabilities"""
        return OutputCapability.REPORT
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ModuleResult:
        """
        Execute report generation
        
        Args:
            parameters: Generation parameters
                - question: Original quiz question (required)
                - statistics: Statistical results
                - insights: Analysis insights
                - chart_base64: Chart image (if any)
                - format: Output format (text, markdown, json, html)
            context: Execution context
            
        Returns:
            ModuleResult: Report result
        """
        question = parameters.get('question')
        
        if not question:
            return ModuleResult(
                success=False,
                error="Question parameter is required"
            )
        
        logger.info(f"[REPORT GENERATOR] Generating answer for: '{question}'")
        
        start_time = time.time()
        
        # Generate report
        result = await self.generate(
            data={
                'question': question,
                'statistics': parameters.get('statistics', {}),
                'insights': parameters.get('insights', {}),
                'chart_base64': parameters.get('chart_base64')
            },
            options={
                'format': parameters.get('format', 'text')
            }
        )
        
        execution_time = time.time() - start_time
        
        if result.success:
            return ModuleResult(
                success=True,
                data={
                    'answer': result.answer,
                    'formatted_answers': result.formatted_answer,
                    'word_count': result.word_count
                },
                metadata={
                    'format': result.format,
                    'has_statistics': result.has_statistics,
                    'has_insights': result.has_insights,
                    'has_chart': result.has_chart
                },
                execution_time=execution_time
            )
        else:
            return ModuleResult(
                success=False,
                error=result.error,
                execution_time=execution_time
            )
    
    async def generate(
        self,
        data: Any,
        options: Optional[Dict[str, Any]] = None
    ) -> ReportResult:
        """
        Generate final answer
        
        Args:
            data: Data to generate report from
                - question: Quiz question
                - statistics: Statistical results
                - insights: Analysis insights
                - chart_base64: Chart image
            options: Generation options
                - format: Output format
            
        Returns:
            ReportResult
        """
        options = options or {}
        
        question = data.get('question', '')
        statistics = data.get('statistics', {})
        insights = data.get('insights', {})
        chart_base64 = data.get('chart_base64')
        
        output_format = options.get('format', 'text')
        
        logger.info(f"Generating answer in {output_format} format")
        
        # Format statistics for prompt
        stats_text = self._format_statistics(statistics)
        
        # Format insights for prompt
        insights_text = self._format_insights(insights)
        
        # Build prompt
        prompt = ReportPrompts.answer_generation_prompt(
            question=question,
            statistics=stats_text,
            insights=insights_text,
            has_chart=bool(chart_base64),
            format_type=output_format
        )
        
        # Generate answer using LLM
        try:
            answer = await self.llm_client.run_agent(
                self._answer_agent,
                prompt
            )
            
            # Convert to dict
            answer_dict = answer.model_dump()
            
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            answer_dict = self._get_fallback_answer(question)
        
        # Add metadata
        answer_dict['question'] = question
        answer_dict['has_chart'] = bool(chart_base64)
        answer_dict['chart_base64'] = chart_base64
        answer_dict['confidence_level'] = insights.get('confidence_level', 'medium')
        
        # Format in multiple formats
        formatted_answers = {
            'text': self.formatter.format_as_text(answer_dict),
            'markdown': self.formatter.format_as_markdown(answer_dict),
            'json': self.formatter.format_as_json(answer_dict),
            'html': self.formatter.format_as_html(answer_dict)
        }
        
        # Get requested format
        final_answer = formatted_answers.get(output_format, formatted_answers['text'])
        
        # Calculate word count
        word_count = len(final_answer.split())
        
        logger.info(f"✓ Answer generated: {word_count} words")
        
        return ReportResult(
            success=True,
            answer=final_answer,
            formatted_answer=formatted_answers,
            has_statistics=bool(statistics),
            has_insights=bool(insights),
            has_chart=bool(chart_base64),
            format=OutputFormat(output_format),
            word_count=word_count
        )
    
    def _format_statistics(self, statistics: Dict[str, Any]) -> str:
        """Format statistics for prompt"""
        if not statistics:
            return "No statistical analysis available."
        
        lines = []
        
        if 'descriptive' in statistics:
            lines.append("Descriptive Statistics:")
            for column, stats in statistics['descriptive'].items():
                lines.append(f"  {column}: mean={stats.get('mean')}, median={stats.get('median')}, std={stats.get('std')}")
        
        if 'correlations' in statistics:
            lines.append("\nCorrelations:")
            for pair, corr in statistics['correlations'].items():
                lines.append(f"  {pair}: {corr.get('coefficient')} ({corr.get('strength')} {corr.get('direction')})")
        
        if 'segments' in statistics:
            lines.append("\nSegment Analysis:")
            for segment, data in statistics['segments'].items():
                lines.append(f"  {segment}: {data}")
        
        if 'trends' in statistics:
            lines.append("\nTrends:")
            trend = statistics['trends'].get('trend', {})
            lines.append(f"  Direction: {trend.get('direction')}, Growth: {trend.get('growth_rate')}")
        
        return "\n".join(lines) if lines else "No statistics available."
    
    def _format_insights(self, insights: Dict[str, Any]) -> str:
        """Format insights for prompt"""
        if not insights:
            return "No insights available."
        
        lines = []
        
        if 'direct_answer' in insights:
            lines.append(f"Direct Answer: {insights['direct_answer']}")
        
        if 'key_findings' in insights:
            lines.append("\nKey Findings:")
            for finding in insights['key_findings']:
                lines.append(f"  - {finding}")
        
        if 'recommendations' in insights:
            lines.append("\nRecommendations:")
            for rec in insights['recommendations']:
                lines.append(f"  - {rec}")
        
        return "\n".join(lines) if lines else "No insights available."
    
    def _get_fallback_answer(self, question: str) -> Dict[str, Any]:
        """Fallback answer if LLM fails"""
        return {
            "direct_answer": f"Analysis completed for the question: {question}",
            "key_findings": [
                "Statistical analysis has been performed",
                "Data has been processed and analyzed"
            ],
            "supporting_evidence": [
                "Results based on available data"
            ],
            "recommendations": [
                "Review the detailed statistical results",
                "Consider additional data sources if available"
            ]
        }
