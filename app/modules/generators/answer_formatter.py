"""
Answer Formatter
Formats answers in different output formats
"""

from typing import Dict, Any
import json

from app.core.logging import get_logger

logger = get_logger(__name__)


class AnswerFormatter:
    """
    Formats answers in multiple output formats
    """
    
    @staticmethod
    def format_as_text(answer_data: Dict[str, Any]) -> str:
        """
        Format as plain text
        
        Args:
            answer_data: Answer components
            
        Returns:
            Plain text answer
        """
        parts = []
        
        # Question
        if answer_data.get('question'):
            parts.append(f"Question: {answer_data['question']}")
            parts.append("")
        
        # Direct answer
        if answer_data.get('direct_answer'):
            parts.append("Answer:")
            parts.append(answer_data['direct_answer'])
            parts.append("")
        
        # Key findings
        if answer_data.get('key_findings'):
            parts.append("Key Findings:")
            for i, finding in enumerate(answer_data['key_findings'], 1):
                parts.append(f"{i}. {finding}")
            parts.append("")
        
        # Supporting evidence
        if answer_data.get('supporting_evidence'):
            parts.append("Supporting Evidence:")
            for evidence in answer_data['supporting_evidence']:
                parts.append(f"• {evidence}")
            parts.append("")
        
        # Recommendations
        if answer_data.get('recommendations'):
            parts.append("Recommendations:")
            for i, rec in enumerate(answer_data['recommendations'], 1):
                parts.append(f"{i}. {rec}")
            parts.append("")
        
        # Chart note
        if answer_data.get('has_chart'):
            parts.append("[Chart: See visualization above]")
            parts.append("")
        
        # Confidence
        if answer_data.get('confidence_level'):
            parts.append(f"Confidence Level: {answer_data['confidence_level']}")
        
        return "\n".join(parts)
    
    @staticmethod
    def format_as_markdown(answer_data: Dict[str, Any]) -> str:
        """
        Format as Markdown
        
        Args:
            answer_data: Answer components
            
        Returns:
            Markdown answer
        """
        parts = []
        
        # Question
        if answer_data.get('question'):
            parts.append(f"# {answer_data['question']}")
            parts.append("")
        
        # Direct answer
        if answer_data.get('direct_answer'):
            parts.append("## Answer")
            parts.append("")
            parts.append(answer_data['direct_answer'])
            parts.append("")
        
        # Key findings
        if answer_data.get('key_findings'):
            parts.append("## Key Findings")
            parts.append("")
            for finding in answer_data['key_findings']:
                parts.append(f"- {finding}")
            parts.append("")
        
        # Supporting evidence
        if answer_data.get('supporting_evidence'):
            parts.append("## Supporting Evidence")
            parts.append("")
            for evidence in answer_data['supporting_evidence']:
                parts.append(f"- {evidence}")
            parts.append("")
        
        # Recommendations
        if answer_data.get('recommendations'):
            parts.append("## Recommendations")
            parts.append("")
            for i, rec in enumerate(answer_data['recommendations'], 1):
                parts.append(f"{i}. {rec}")
            parts.append("")
        
        # Chart
        if answer_data.get('chart_base64'):
            parts.append("## Visualization")
            parts.append("")
            parts.append(f"![Chart](data:image/png;base64,{answer_data['chart_base64']})")
            parts.append("")
        
        # Confidence
        if answer_data.get('confidence_level'):
            parts.append("---")
            parts.append("")
            parts.append(f"**Confidence Level:** {answer_data['confidence_level']}")
        
        return "\n".join(parts)
    
    @staticmethod
    def format_as_json(answer_data: Dict[str, Any]) -> str:
        """
        Format as JSON
        
        Args:
            answer_data: Answer components
            
        Returns:
            JSON string
        """
        return json.dumps(answer_data, indent=2)
    
    @staticmethod
    def format_as_html(answer_data: Dict[str, Any]) -> str:
        """
        Format as HTML
        
        Args:
            answer_data: Answer components
            
        Returns:
            HTML string
        """
        html_parts = ['<div class="quiz-answer">']
        
        # Question
        if answer_data.get('question'):
            html_parts.append(f'<h1>{answer_data["question"]}</h1>')
        
        # Direct answer
        if answer_data.get('direct_answer'):
            html_parts.append('<div class="direct-answer">')
            html_parts.append(f'<h2>Answer</h2>')
            html_parts.append(f'<p>{answer_data["direct_answer"]}</p>')
            html_parts.append('</div>')
        
        # Key findings
        if answer_data.get('key_findings'):
            html_parts.append('<div class="key-findings">')
            html_parts.append('<h2>Key Findings</h2>')
            html_parts.append('<ul>')
            for finding in answer_data['key_findings']:
                html_parts.append(f'<li>{finding}</li>')
            html_parts.append('</ul>')
            html_parts.append('</div>')
        
        # Supporting evidence
        if answer_data.get('supporting_evidence'):
            html_parts.append('<div class="supporting-evidence">')
            html_parts.append('<h2>Supporting Evidence</h2>')
            html_parts.append('<ul>')
            for evidence in answer_data['supporting_evidence']:
                html_parts.append(f'<li>{evidence}</li>')
            html_parts.append('</ul>')
            html_parts.append('</div>')
        
        # Recommendations
        if answer_data.get('recommendations'):
            html_parts.append('<div class="recommendations">')
            html_parts.append('<h2>Recommendations</h2>')
            html_parts.append('<ol>')
            for rec in answer_data['recommendations']:
                html_parts.append(f'<li>{rec}</li>')
            html_parts.append('</ol>')
            html_parts.append('</div>')
        
        # Chart
        if answer_data.get('chart_base64'):
            html_parts.append('<div class="chart">')
            html_parts.append('<h2>Visualization</h2>')
            html_parts.append(f'<img src="data:image/png;base64,{answer_data["chart_base64"]}" alt="Chart" />')
            html_parts.append('</div>')
        
        # Confidence
        if answer_data.get('confidence_level'):
            html_parts.append('<div class="confidence">')
            html_parts.append(f'<p><strong>Confidence Level:</strong> {answer_data["confidence_level"]}</p>')
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
