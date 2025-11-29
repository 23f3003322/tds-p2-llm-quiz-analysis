"""
Module Registry
Central registry for all processing modules
Handles module registration, discovery, and selection
"""

from typing import Dict, List, Optional, Type, Set
from collections import defaultdict

from app.modules.base import BaseModule, ModuleType, ModuleCapability
from app.orchestrator.parameter_models import ExtractedParameters
from app.orchestrator.models import TaskClassification
from app.core.logging import get_logger

logger = get_logger(__name__)

class ModuleRegistry:
    """
    Central registry for all processing modules
    Singleton pattern - only one registry exists
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize module registry"""
        if self._initialized:
            return
        
        self.modules: Dict[str, BaseModule] = {}
        self.modules_by_type: Dict[ModuleType, List[BaseModule]] = defaultdict(list)
        self._initialized = True
        
        logger.info("ModuleRegistry initialized")
    
    def register(self, module: BaseModule):
        """
        Register a module
        
        Args:
            module: Module to register
        """
        if module.name in self.modules:
            logger.warning(f"Module '{module.name}' already registered, replacing")
        
        self.modules[module.name] = module
        self.modules_by_type[module.module_type].append(module)
        
        logger.info(
            f"✓ Registered module: {module.name} "
            f"(type: {module.module_type.value})"
        )
    
    def unregister(self, module_name: str) -> bool:
        """
        Unregister a module
        
        Args:
            module_name: Name of module to unregister
            
        Returns:
            bool: True if unregistered
        """
        if module_name not in self.modules:
            return False
        
        module = self.modules[module_name]
        del self.modules[module_name]
        self.modules_by_type[module.module_type].remove(module)
        
        logger.info(f"Unregistered module: {module_name}")
        return True
    
    def get_module(self, name: str) -> Optional[BaseModule]:
        """Get module by name"""
        return self.modules.get(name)
    
    def get_modules_by_type(self, module_type: ModuleType) -> List[BaseModule]:
        """Get all modules of a specific type"""
        return self.modules_by_type.get(module_type, [])
    
    def get_all_modules(self) -> List[BaseModule]:
        """Get all registered modules"""
        return list(self.modules.values())
    
    def list_modules(self) -> Dict[str, Dict]:
        """
        List all registered modules with their info
        
        Returns:
            Dict: Module information
        """
        result = {}
        
        for name, module in self.modules.items():
            capabilities = module.get_capabilities()
            
            result[name] = {
                'type': module.module_type.value,
                'initialized': module.is_initialized(),
                'capabilities': capabilities.dict()
            }
        
        return result
    
    def clear(self):
        """Clear all registered modules (for testing)"""
        self.modules.clear()
        self.modules_by_type.clear()
        logger.info("Registry cleared")

class ModuleSelector:
    """
    Selects appropriate modules based on task requirements
    Uses classification and parameters to find best modules
    """
    
    def __init__(self, registry: Optional[ModuleRegistry] = None):
        """
        Initialize module selector
        
        Args:
            registry: Module registry to use (creates new if None)
        """
        self.registry = registry or ModuleRegistry()
        logger.debug("ModuleSelector initialized")
    
    def select_by_capability(self, capability: str) -> Optional[BaseModule]:
        """
        Select FIRST module that supports a specific capability
        Fast lookup for instruction-driven execution
        """
        logger.debug(f"🔍 Selecting module by capability: {capability}")
        
        for module in self.registry.get_all_modules():
            capabilities = module.get_capabilities()
            
            # Check if capability is directly supported (boolean field)
            if hasattr(capabilities, capability) and getattr(capabilities, capability):
                logger.info(f"✓ Selected {module.name} for capability '{capability}'")
                return module
            
            # Also check list-based capabilities if exist
            if hasattr(capabilities, 'capabilities'):
                caps_attr = getattr(capabilities, 'capabilities')
                if isinstance(caps_attr, (list, set, tuple)) and capability in caps_attr:
                    logger.info(f"✓ Selected {module.name} for capability '{capability}'")
                    return module
        
        logger.warning(f"No module found for capability: {capability}")
        return None
    
    def select_modules(
        self,
        classification: TaskClassification,
        parameters: ExtractedParameters
    ) -> List[BaseModule]:
        """
        Select appropriate modules for task
        
        Args:
            classification: Task classification
            parameters: Extracted parameters
            
        Returns:
            List[BaseModule]: Selected modules in execution order
        """
        logger.info("🔍 Selecting modules for task")
        logger.debug(
            f"Task type: {classification.primary_task.value}, "
            f"Complexity: {classification.complexity.value}"
        )
        
        selected = []
        
        # Step 1: Select data sourcing module
        sourcing_module = self._select_sourcing_module(classification, parameters)
        if sourcing_module:
            selected.append(sourcing_module)
        
        # Step 2: Select processing modules
        processing_modules = self._select_processing_modules(classification, parameters)
        selected.extend(processing_modules)
        
        # Step 3: Select visualization module (if needed)
        viz_module = self._select_visualization_module(classification, parameters)
        if viz_module:
            selected.append(viz_module)
        
        # Step 4: Select output/export module
        output_module = self._select_output_module(classification, parameters)
        if output_module:
            selected.append(output_module)
        
        logger.info(
            f"✅ Selected {len(selected)} modules: "
            f"{[m.name for m in selected]}"
        )
        
        return selected
    
    def _select_sourcing_module(
        self,
        classification: TaskClassification,
        parameters: ExtractedParameters
    ) -> Optional[BaseModule]:
        """Select data sourcing module (scraper, API client, etc.)"""
        
        # No data sources, no module needed
        if not parameters.data_sources:
            logger.debug("No data sources, skipping sourcing module")
            return None
        
        data_source = parameters.data_sources[0]  # Use first source
        
        # API data source
        if data_source.type == 'api':
            logger.debug("Selecting API client module")
            candidates = self.registry.get_modules_by_type(ModuleType.API_CLIENT)
            
            for module in candidates:
                if module.get_capabilities().can_handle_api:
                    logger.info(f"✓ Selected API client: {module.name}")
                    return module
        
        # URL/web scraping
        if data_source.type == 'url':
            # Check if JavaScript needed from CLASSIFICATION (primary source)
            needs_javascript = classification.requires_javascript  # ← Fixed: Check classification first
            
            # Also check parameters.urls if present
            if parameters.urls:
                needs_javascript = needs_javascript or any(
                    u.requires_javascript for u in parameters.urls
                )
            
            if needs_javascript:
                logger.debug("JavaScript required, selecting dynamic scraper")
                candidates = self.registry.get_modules_by_type(ModuleType.SCRAPER)
                
                for module in candidates:
                    if module.get_capabilities().can_scrape_dynamic:
                        logger.info(f"✓ Selected dynamic scraper: {module.name}")
                        return module
                
                logger.warning("JavaScript needed but no dynamic scraper available")
            
            # Static HTML scraping
            logger.debug("Selecting static scraper")
            candidates = self.registry.get_modules_by_type(ModuleType.SCRAPER)
            
            for module in candidates:
                if module.get_capabilities().can_scrape_static:
                    logger.info(f"✓ Selected static scraper: {module.name}")
                    return module
        
        logger.warning("No suitable sourcing module found")
        return None
    
    def _select_processing_modules(
        self,
        classification: TaskClassification,
        parameters: ExtractedParameters
    ) -> List[BaseModule]:
        """Select data processing modules"""
        
        selected = []
        
        # Data cleaning (if filters present)
        if parameters.filters:
            logger.debug("Filters detected, need data processor")
            candidates = self.registry.get_modules_by_type(ModuleType.PROCESSOR)
            
            for module in candidates:
                caps = module.get_capabilities()
                if caps.can_filter or caps.can_transform_data:
                    logger.info(f"✓ Selected processor: {module.name}")
                    selected.append(module)
                    break
        
        # Aggregation (if aggregations present)
        if parameters.aggregations:
            logger.debug("Aggregations detected")
            candidates = self.registry.get_modules_by_type(ModuleType.PROCESSOR)
            
            for module in candidates:
                if module.get_capabilities().can_aggregate:
                    if module not in selected:
                        logger.info(f"✓ Selected aggregator: {module.name}")
                        selected.append(module)
                    break
        
        return selected
    
    def _select_visualization_module(
        self,
        classification: TaskClassification,
        parameters: ExtractedParameters
    ) -> Optional[BaseModule]:
        """Select visualization module"""
        
        if not parameters.visualizations:
            return None
        
        viz_req = parameters.visualizations[0]  # Use first visualization
        
        # Map visualization
        if viz_req.type == 'map':
            logger.debug("Map visualization needed")
            candidates = self.registry.get_modules_by_type(ModuleType.VISUALIZER)
            
            for module in candidates:
                if module.get_capabilities().can_create_maps:
                    logger.info(f"✓ Selected map creator: {module.name}")
                    return module
        
        # Chart visualization
        if viz_req.type == 'chart':
            logger.debug("Chart visualization needed")
            candidates = self.registry.get_modules_by_type(ModuleType.VISUALIZER)
            
            for module in candidates:
                if module.get_capabilities().can_create_charts:
                    logger.info(f"✓ Selected chart creator: {module.name}")
                    return module
        
        return None
    
    def _select_output_module(
        self,
        classification: TaskClassification,
        parameters: ExtractedParameters
    ) -> Optional[BaseModule]:
        """Select output/export module"""
        
        if not parameters.output:
            logger.debug("No output format specified, using default CSV")
            output_format = 'csv'
        else:
            output_format = parameters.output.format
        
        candidates = self.registry.get_modules_by_type(ModuleType.EXPORTER)
        
        # Match by format
        for module in candidates:
            caps = module.get_capabilities()
            
            if output_format == 'csv' and caps.can_export_csv:
                logger.info(f"✓ Selected CSV exporter: {module.name}")
                return module
            
            elif output_format == 'excel' and caps.can_export_excel:
                logger.info(f"✓ Selected Excel exporter: {module.name}")
                return module
            
            elif output_format == 'json' and caps.can_export_json:
                logger.info(f"✓ Selected JSON exporter: {module.name}")
                return module
        
        logger.warning(f"No exporter for format: {output_format}")
        return None
    
    def can_execute_task(
        self,
        classification: TaskClassification,
        parameters: ExtractedParameters
    ) -> bool:
        """
        Check if task can be executed with available modules
        
        Args:
            classification: Task classification
            parameters: Extracted parameters
            
        Returns:
            bool: True if task can be executed
        """
        selected = self.select_modules(classification, parameters)
        
        # Need at least one module to execute
        if not selected:
            logger.warning("No modules selected, cannot execute task")
            return False
        
        # Check if we have sourcing module (if data sources present)
        if parameters.data_sources and not any(
            m.module_type in [ModuleType.SCRAPER, ModuleType.API_CLIENT] 
            for m in selected
        ):
            logger.warning("Data sources present but no sourcing module")
            return False
        
        return True

# Convenience function
def get_module_registry() -> ModuleRegistry:
    """Get global module registry instance"""
    return ModuleRegistry()

def get_module_selector() -> ModuleSelector:
    """Get module selector instance"""
    return ModuleSelector()
