"""
Report Generation Modules
Final answer generation for quiz questions
"""

from app.modules.generators.base_generator import BaseGenerator, ReportResult
from app.modules.generators.report_generator import ReportGenerator

__all__ = [
    "BaseGenerator",
    "ReportResult",
    "ReportGenerator"
]
