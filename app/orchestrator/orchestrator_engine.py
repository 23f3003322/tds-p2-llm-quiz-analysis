"""
Orchestrator Engine - Instruction-Driven Execution
Uses parsed instructions from TaskFetcher, only required modules
"""

import re
from typing import Dict, Any, Optional, List
import time
import asyncio
from urllib.parse import urljoin

from app.orchestrator.execution_context import ExecutionContext
from app.orchestrator.models import UnifiedTaskAnalysis
from app.modules.registry import ModuleRegistry, ModuleSelector
from app.services.task_fetcher import TaskFetcher
from app.core.logging import get_logger
from app.core.exceptions import TaskProcessingError

logger = get_logger(__name__)

class OrchestratorEngine:
    """
    Instruction-driven orchestrator
    Executes ONLY the modules required by parsed instructions
    """
    
    def __init__(self, module_registry: Optional[ModuleRegistry] = None):
        self.task_fetcher = TaskFetcher()
        self.registry = module_registry or ModuleRegistry()
        self.module_selector = ModuleSelector(self.registry)
        logger.info(f"🚀 Instruction-driven Orchestrator initialized")
        logger.info(f"   Modules available: {len(self.registry.get_all_modules())}")
    
    async def execute_task(
        self,
        task_input: str,
        task_url: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute task using parsed instructions (fast path) or full pipeline (fallback)
        """
        exec_context = ExecutionContext(
            original_task=task_input,
            task_url=task_url,
            metadata=context or {}
        )
        
        logger.info("=" * 80)
        logger.info("🎯 INSTRUCTION-DRIVEN ORCHESTRATOR")
        logger.info(f"Task: {task_input[:100]}...")
        logger.info("=" * 80)
        
        try:
            # ✅ PRIORITY 1: Check if we have pre-parsed instructions from TaskFetcher
            instructions = context.get('instructions', []) if context else []
            submission_url = context.get('submission_url') if context else None
            
            if instructions:
                logger.info(f"📋 Found {len(instructions)} pre-parsed instructions - FAST PATH")
                result = await self._execute_from_instructions(
                    instructions=instructions,
                    task_description=task_input,
                    submission_url=submission_url,
                    task_url=task_url,
                    exec_context=exec_context
                )
            else:
                logger.info("🔍 No instructions found - FULL PIPELINE (legacy)")
                result = await self._execute_full_pipeline(task_input, task_url, exec_context)
            
            exec_context.mark_completed()
            final_result = self._build_final_result(result, exec_context)
            
            logger.info("=" * 80)
            logger.info(f"✅ EXECUTION COMPLETE | {exec_context.get_duration():.2f}s")
            return final_result
            
        except Exception as e:
            exec_context.mark_failed(str(e))
            logger.error(f"❌ Orchestration failed: {str(e)}", exc_info=True)
            return self._build_error_result(exec_context, str(e))
    
    async def _execute_from_instructions(
        self,
        instructions: List[Dict[str, Any]],
        task_description: str,
        submission_url: Optional[str],
        task_url: Optional[str],
        exec_context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute ONLY required modules based on instructions"""
        logger.info("🚀 FAST PATH: Instruction-driven execution")
        exec_context.log_event("Instruction execution started")
        
        # Execution state
        state = {
            'scraped_data': {},
            'extracted_values': {},
            'processed_data': None,
            'visualizations': [],
            'final_answer': None
        }
        
        for step in instructions:
            step_num = step.get('step', 0)
            action = step.get('action')
            target = step.get('target')
            description = step.get('text', '')
            
            logger.info(f"📍 Step {step_num}: {action} ({target or description[:50]}...)")
            exec_context.log_event(f"Step {step_num}: {action}")
            
            try:
                if action == 'scrape':
                    result = await self._execute_scrape(target, task_url, exec_context)
                    state['scraped_data'][target or f'step_{step_num}'] = result
                    
                elif action == 'extract':
                    value = await self._execute_extract(state, step, exec_context)
                    state['extracted_values'][step_num] = value
                    
                elif action == 'calculate':
                    value = await self._execute_calculate(description, exec_context)
                    state['final_answer'] = value
                    
                elif action == 'analyze':
                    state['processed_data'] = await self._execute_analysis(state, step, exec_context)
                    
                elif action == 'visualize':
                    viz = await self._execute_visualize(state, step, exec_context)
                    state['visualizations'].append(viz)
                    
                elif action == 'generate':
                    state['final_answer'] = await self._execute_generate(state, step, exec_context)
                    
                elif action == 'submit':
                    # Select a module capable of submitting/exporting results
                    submitter = self.module_selector.select_by_capability('can_export_json')
                    if submitter:
                        payload = {
                            'submission_url': submission_url,
                            'email': exec_context.metadata.get('email'),
                            'secret': state.get('final_answer'),
                            'quiz_url': task_url,
                            'answer': state.get('final_answer')
                        }
                        result = await submitter.execute(payload)
                        logger.info(f"📤 Submission result: {getattr(result, 'success', False)}, data: {getattr(result, 'data', None)}")
                        state['submission_result'] = getattr(result, 'data', None)
                    else:
                        logger.warning("No submitter module available for 'submit' action")
                else:
                    logger.debug(f"Unknown action '{action}' - skipping")
            
            except Exception as e:
                logger.error(f"✗ Step {step_num} failed: {e}", exc_info=True)
                exec_context.log_event(f"Step {step_num} failed: {str(e)}")
                # Continue to next step without aborting entire instruction set
                continue
        
        # Ensure final answer exists
        if state.get('final_answer') is None:
            state['final_answer'] = self._get_best_answer(state)
        
        modules_used = self._get_modules_used(exec_context)
        
        return {
            'strategy': 'instructions',
            'success': state['final_answer'] is not None,
            'modules_used': modules_used,
            'data': state,
            'submission_url': submission_url,
            'steps_executed': len(instructions)
        }
    
    async def _execute_full_pipeline(
        self,
        task_input: str,
        task_url: Optional[str],
        exec_context: ExecutionContext
    ) -> Dict[str, Any]:
        """Fallback: Legacy full pipeline (for backward compatibility)"""
        logger.warning("⚠️  Using legacy full pipeline")
        return {
            'strategy': 'legacy',
            'success': False,
            'data': {'error': 'Legacy pipeline not implemented for instructions'},
            'modules_used': []
        }
    
    # =========================================================================
    # MODULE EXECUTION HELPERS (✅ FIXED CAPABILITY NAMES)
    # =========================================================================
    
    async def _execute_scrape(self, target_url: str, base_url: str, exec_context: ExecutionContext) -> Dict:
        """Execute scraping with appropriate scraper"""
        url = urljoin(base_url or '', target_url)
        logger.info(f"🌐 Scraping: {url}")
        
        # ✅ FIXED: Try static first
        static_module = self.module_selector.select_by_capability('can_scrape_static')
        if static_module:
            result = await static_module.execute({'url': url})
            if result.success and result.data:
                logger.info(f"✓ Static scrape succeeded ({len(result.data) if isinstance(result.data, (list, dict)) else 'content'})")
                return result.data
        
        # ✅ FIXED: Fallback to dynamic
        dynamic_module = self.module_selector.select_by_capability('can_scrape_dynamic')
        if dynamic_module:
            result = await dynamic_module.execute({'url': url})
            logger.info(f"✓ Dynamic scrape: {result.success}")
            return result.data if result.success else {}
        
        raise TaskProcessingError(f"Could not scrape {url}")
    
    async def _execute_extract(self, state: Dict, step: Dict, exec_context: ExecutionContext) -> Any:
        """Extract specific data from scraped content"""
        logger.info("🔍 Extracting data")
        
        scraped = list(state['scraped_data'].values())
        if not scraped:
            raise TaskProcessingError("No scraped data for extraction")
        
        # ✅ FIXED: Look for extraction modules
        extractor = self.module_selector.select_by_capability('can_extract_data')
        if extractor:
            latest_scrape = scraped[-1]
            result = await extractor.execute({
                'data': latest_scrape,
                'target': step.get('target', 'secret code')
            })
            return result.data if result.success else None
        
        # Fallback: simple text search
        target = step.get('target', '').lower()
        for scrape_data in scraped:
            if isinstance(scrape_data, dict):
                for key, value in scrape_data.items():
                    if target in str(value).lower():
                        logger.info(f"✓ Extracted: {value}")
                        return value
        raise TaskProcessingError("Extraction failed")
    
    async def _execute_calculate(self, description: str, exec_context: ExecutionContext) -> Any:
        """Execute calculation"""
        logger.info(f"🧮 Calculating: {description}")
        
        # ✅ FIXED
        calc_module = self.module_selector.select_by_capability('can_calculate')
        if calc_module:
            result = await calc_module.execute({'expression': description})
            return result.data if result.success else None
        
        # Simple eval fallback (secure context only)
        try:
            safe_desc = re.sub(r'[^\d+\-*/().\s]', '', description)
            result = eval(safe_desc)
            return result
        except:
            raise TaskProcessingError(f"Calculation failed: {description}")
    
    async def _execute_analysis(self, state: Dict, step: Dict, exec_context: ExecutionContext) -> Dict:
        """Execute data analysis ONLY when instructed"""
        logger.info("📊 Analyzing data")
        
        # ✅ FIXED
        analyzer = self.module_selector.select_by_capability('can_analyze_data')
        if analyzer:
            result = await analyzer.execute({'data': state['scraped_data']})
            return result.data if result.success else {}
        return {}
    
    async def _execute_visualize(self, state: Dict, step: Dict, exec_context: ExecutionContext) -> Dict:
        """Execute visualization ONLY when instructed"""
        logger.info("📈 Creating visualization")
        
        # ✅ FIXED
        visualizer = self.module_selector.select_by_capability('can_create_charts')
        if visualizer:
            result = await visualizer.execute({'data': state['scraped_data']})
            return result.data if result.success else {}
        return {}
    
    async def _execute_generate(self, state: Dict, step: Dict, exec_context: ExecutionContext) -> Any:
        """Generate final answer ONLY when instructed"""
        logger.info("✍️ Generating final answer")
        
        # ✅ FIXED
        generator = self.module_selector.select_by_capability('can_generate_answers')
        if generator:
            result = await generator.execute(state)
            return result.data if result.success else None
        return self._get_best_answer(state)
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    def _get_best_answer(self, state: Dict) -> Any:
        """Get the best available answer from state"""
        if state.get('final_answer'):
            return state['final_answer']
        if state.get('extracted_values'):
            return list(state['extracted_values'].values())[-1]
        if state.get('processed_data'):
            return state['processed_data']
        return "No answer found"
    
    def _get_modules_used(self, exec_context: ExecutionContext) -> List[str]:
        """Get list of modules actually used - ROBUST VERSION"""
        modules = set()
        
        if not exec_context.execution_log:
            return []
        
        for event in exec_context.execution_log:
            if isinstance(event, dict):
                details = event.get('details', {})
                if isinstance(details, dict) and 'module' in details:
                    modules.add(details['module'])
            elif isinstance(event, str):
                continue
        
        return list(modules)
    
    def _build_final_result(self, execution_result: Dict, context: ExecutionContext) -> Dict:
        """Build standardized result"""
        return {
            'success': execution_result.get('success', False),
            'task_id': context.task_id,
            'execution_id': context.execution_id,
            'answer': execution_result['data'].get('final_answer'),
            'modules_used': execution_result.get('modules_used', []),
            'strategy': execution_result.get('strategy'),
            'duration': context.get_duration(),
            'submission_url': execution_result.get('submission_url'),
            'data': execution_result['data'],
            'execution_log': context.execution_log
        }
    
    def _build_error_result(self, context: ExecutionContext, error: str) -> Dict:
        """Build error result"""
        return {
            'success': False,
            'task_id': context.task_id,
            'execution_id': context.execution_id,
            'error': error,
            'duration': context.get_duration(),
            'execution_log': context.execution_log
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.task_fetcher.__aexit__(None, None, None)
        logger.info("Orchestrator cleanup complete")
