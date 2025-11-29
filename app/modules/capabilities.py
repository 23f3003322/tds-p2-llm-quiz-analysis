"""
Module Capability Definitions
Pre-defined capability sets for different module types
"""

from app.modules.base import ModuleCapability,ModuleType


class ScrapingCapability:
    """Capability definitions for scraping modules"""
    
    STATIC = ModuleCapability(
        can_scrape_static=True,
        can_scrape_dynamic=False,
        can_handle_javascript=False,
        can_authenticate=False,
        supported_input_formats={'html', 'xml'},
        supported_output_formats={'json', 'csv', 'dict'},
        max_concurrent_requests=5,
        estimated_speed="fast",
        memory_usage="low",
        requires_browser=False
    )
    
    DYNAMIC = ModuleCapability(
        can_scrape_static=True,
        can_scrape_dynamic=True,
        can_handle_javascript=True,
        can_authenticate=True,
        supported_input_formats={'html', 'javascript'},
        supported_output_formats={'json', 'csv', 'dict'},
        max_concurrent_requests=2,
        estimated_speed="medium",
        memory_usage="high",
        requires_browser=True
    )
    
    API_CLIENT = ModuleCapability(
        can_handle_api=True,
        supported_input_formats={'api', 'rest', 'graphql'},
        supported_output_formats={'json', 'dict'},
        max_concurrent_requests=10,
        estimated_speed="fast",
        memory_usage="low",
        requires_api_key=True
    )

class DataSourceCapability:
    """Data source capabilities"""
    
    API = ModuleCapability(
        module_type=ModuleType.DATA_SOURCE,
        supported_input_formats={'url', 'endpoint'},
        supported_output_formats={'json', 'xml', 'csv'},
        can_handle_javascript=False,
        requires_browser=False
    )
    
    DATABASE = ModuleCapability(
        module_type=ModuleType.DATA_SOURCE,
        supported_input_formats={'connection_string', 'query'},
        supported_output_formats={'json', 'csv'},
        can_handle_javascript=False,
        requires_browser=False
    )
    
    FILE = ModuleCapability(
        module_type=ModuleType.DATA_SOURCE,
        supported_input_formats={'file_path', 'url'},
        supported_output_formats={'json', 'csv'},
        can_handle_javascript=False,
        requires_browser=False
    )




class ProcessingCapability:
    """Capability definitions for data processing modules"""
    
    DATA_CLEANER = ModuleCapability(
        can_process_data=True,
        can_clean_data=True,
        supported_input_formats={'csv', 'json', 'dict', 'dataframe'},
        supported_output_formats={'csv', 'json', 'dict', 'dataframe'},
        max_concurrent_requests=1,
        estimated_speed="fast",
        memory_usage="medium"
    )
    
    DATA_TRANSFORMER = ModuleCapability(
        can_process_data=True,
        can_transform_data=True,
        can_aggregate=True,
        can_filter=True,
        can_sort=True,
        supported_input_formats={'csv', 'json', 'dict', 'dataframe'},
        supported_output_formats={'csv', 'json', 'dict', 'dataframe'},
        max_concurrent_requests=1,
        estimated_speed="medium",
        memory_usage="medium"
    )

class ExtractionCapability:
    """Data extraction capabilities"""
    DATA_EXTRACTOR = ModuleCapability(
        can_extract_data=True,
        supported_input_formats={'html', 'json', 'text', 'csv'},
        supported_output_formats={'dict', 'json', 'text'},
        estimated_speed="fast",
        memory_usage="low"
    )

class CalculationCapability:
    """Calculation capabilities"""
    CALCULATOR = ModuleCapability(
        can_calculate=True,
        supported_input_formats={'expression', 'numbers', 'formula'},
        supported_output_formats={'number', 'json'},
        estimated_speed="fast",
        memory_usage="low"
    )

class GenerationCapability:
    """Answer generation capabilities"""
    ANSWER_GENERATOR = ModuleCapability(
        can_generate_answers=True,
        can_generate_reports=True,
        supported_input_formats={'data', 'analysis', 'scraped_content'},
        supported_output_formats={'text', 'json', 'html'},
        estimated_speed="medium",
        memory_usage="medium"
    )

class AnalysisCapability:
    """Data analysis capabilities"""
    DATA_ANALYZER = ModuleCapability(
        can_analyze_data=True,
        can_run_statistics=True,
        supported_input_formats={'csv', 'json', 'dataframe'},
        supported_output_formats={'json', 'dict', 'text'},
        estimated_speed="medium",
        memory_usage="medium"
    )

class VisualizationCapability:
    """Capability definitions for visualization modules"""
    
    CHART_CREATOR = ModuleCapability(
        can_visualize=True,
        can_create_charts=True,
        supported_input_formats={'csv', 'json', 'dict', 'dataframe'},
        supported_output_formats={'png', 'jpg', 'svg', 'html'},
        max_concurrent_requests=1,
        estimated_speed="medium",
        memory_usage="medium"
    )
    
    MAP_CREATOR = ModuleCapability(
        can_visualize=True,
        can_create_maps=True,
        supported_input_formats={'csv', 'json', 'dict', 'geojson'},
        supported_output_formats={'html', 'png'},
        max_concurrent_requests=1,
        estimated_speed="slow",
        memory_usage="high"
    )


class OutputCapability:
    """Capability definitions for output/export modules"""
    
    CSV_EXPORTER = ModuleCapability(
        can_export_csv=True,
        supported_input_formats={'dict', 'list', 'dataframe'},
        supported_output_formats={'csv'},
        max_concurrent_requests=1,
        estimated_speed="fast",
        memory_usage="low"
    )
    
    EXCEL_EXPORTER = ModuleCapability(
        can_export_excel=True,
        supported_input_formats={'dict', 'list', 'dataframe'},
        supported_output_formats={'xlsx', 'xls'},
        max_concurrent_requests=1,
        estimated_speed="medium",
        memory_usage="medium"
    )
    
    JSON_EXPORTER = ModuleCapability(
        can_export_json=True,
        supported_input_formats={'dict', 'list', 'dataframe'},
        supported_output_formats={'json'},
        max_concurrent_requests=1,
        estimated_speed="fast",
        memory_usage="low"
    )
