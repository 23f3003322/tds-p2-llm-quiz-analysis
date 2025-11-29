"""
Task Fetcher Service - with Static/Dynamic Scraper fallback
Fetches and extracts task descriptions from URLs
"""

import httpx
import json
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import TaskProcessingError
from app.utils.llm_client import get_llm_client
from app.utils.prompts import AnalysisPrompts

logger = get_logger(__name__)


class TaskFetcher:
    """
    Enhanced service for fetching and extracting task descriptions from URLs.
    Strategy:
      1. httpx (fast)
      2. If content looks JS-only/empty → DynamicScraper
      3. Let orchestrator use Static/Dynamic scrapers later for real data pages
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None
        self.llm_client = get_llm_client()
        
        # Import here to avoid circular imports
        from app.orchestrator.models import UnifiedTaskAnalysis
        
        self._content_analyzer_agent = self.llm_client.create_agent(
            output_type=UnifiedTaskAnalysis,
            system_prompt=(
                "You are an expert at analyzing task content. "
                "You detect redirects, extract submission URLs, and parse instructions."
            ),
            retries=2
        )
        
        logger.debug("TaskFetcher initialized with unified LLM analysis")
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                              '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    # ======================================================================
    # PUBLIC ENTRY POINT
    # ======================================================================

    async def fetch_and_analyze(self, url: str, base_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch URL and perform unified LLM analysis.
        1. httpx + basic extraction
        2. If JS-only / empty → DynamicScraper
        3. LLM: redirect + submission_url + instructions
        """
        logger.info(f"📥 Fetching and analyzing URL: {url}")
        if base_url is None:
            base_url = url
        
        # Step 1: Fetch visible content (with fallback)
        content = await self._fetch_content(url)
        
        logger.debug(f"Task description length after fetch: {len(content['task_description'])}")
        
        # Step 2: Unified LLM analysis
        analysis = await self._analyze_content_with_llm(
            task_description=content['task_description'],
            raw_content=content['raw_content'],
            url=url,
            base_url=base_url
        )
        
        # Merge content + analysis
        result = {
            **content,
            'is_redirect': analysis.is_redirect,
            'question_url': analysis.question_url,
            'submission_url': analysis.submission_url,
            'instructions': self._format_instructions(analysis.instructions),
            'overall_goal': analysis.overall_goal,
            'complexity': analysis.complexity,
            'llm_analysis': {
                'redirect_reasoning': analysis.redirect_reasoning,
                'submission_reasoning': analysis.submission_reasoning,
                'confidence': analysis.confidence,
            }
        }
        
        # Resolve relative submission URL if needed
        if analysis.submission_url and analysis.submission_url_is_relative:
            absolute = str(httpx.URL(base_url).join(analysis.submission_url))
            logger.info(f"✓ Resolved relative submission URL: {analysis.submission_url} → {absolute}")
            result['submission_url'] = absolute
        
        # Resolve relative question URL if needed
        if analysis.question_url and analysis.question_url.startswith('/'):
            absolute_q = str(httpx.URL(base_url).join(analysis.question_url))
            logger.info(f"✓ Resolved relative question URL: {analysis.question_url} → {absolute_q}")
            result['question_url'] = absolute_q
        
        logger.info("✅ Analysis complete:")
        logger.info(f"   Is Redirect: {result['is_redirect']}")
        logger.info(f"   Submission URL: {result['submission_url']}")
        logger.info(f"   Instructions: {len(result['instructions'])} steps")
        logger.info(f"   Complexity: {result['complexity']}")
        
        return result

    # ======================================================================
    # FETCHING WITH FALLBACK TO DYNAMIC SCRAPER
    # ======================================================================

    async def _fetch_content(self, url: str) -> Dict[str, Any]:
        """
        Fetch content from URL.
        - Try httpx first
        - If JS-only/empty → fallback to DynamicScraper
        """
        if not self._is_valid_url(url):
            raise TaskProcessingError(f"Invalid URL format: {url}")
        
        try:
            response = await self._fetch_url(url)
            content_type = self._detect_content_type(response)
            
            # Basic extraction
            task_description = await self._extract_basic_content(response, content_type)
            raw_content = response.text[:5000]
            
            # Heuristic: if nothing useful, try dynamic scraper
            if self._looks_js_only(task_description, raw_content):
                logger.warning("⚠️ Content looks JS-only/empty. Falling back to DynamicScraper for instructions.")
                dyn = await self._fetch_with_dynamic_scraper(url)
                task_description = dyn['task_description']
                raw_content = dyn['raw_content']
            
            return {
                'task_description': task_description,
                'raw_content': raw_content,
                'content_type': content_type,
                'url': url,
                'metadata': {
                    'content_length': len(response.content),
                    'status_code': response.status_code,
                }
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch content: {e}", exc_info=True)
            raise TaskProcessingError(f"Failed to fetch URL: {str(e)}")
    
    async def _fetch_url(self, url: str) -> httpx.Response:
        """Fetch with httpx and retries."""
        max_retries = getattr(settings, "MAX_RETRIES", 3)
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"HTTPX fetch attempt {attempt + 1}/{max_retries} for {url}")
                response = await self.client.get(url)
                response.raise_for_status()
                return response
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                continue

    def _looks_js_only(self, task_description: str, html: str) -> bool:
        """
        Detect JS-only / empty pages that need dynamic rendering.
        - Empty or tiny text
        - Has <script> that uses atob/innerHTML/URLSearchParams
        """
        if task_description and len(task_description.strip()) > 50:
            return False
        
        # Strong JS signals
        js_markers = ['atob(', 'innerHTML', 'URLSearchParams', 'document.querySelector']
        if any(marker in html for marker in js_markers):
            return True
        
        # Very little visible text after stripping scripts
        cleaned = re.sub(r'<script.*?</script>', '', html, flags=re.S | re.I)
        if len(cleaned.strip()) < 100:
            return True
        
        return False

    async def _fetch_with_dynamic_scraper(self, url: str) -> Dict[str, Any]:
        """
        Use DynamicScraper to render the page and extract visible text
        for instruction pages.
        """
        from app.modules.scrapers.dynamic_scraper import DynamicScraper
        
        scraper = DynamicScraper(use_pool=True)
        await scraper.initialize()
        try:
            # Auto-extract text blocks
            result = await scraper.scrape_url(url)
            if not result.success:
                raise RuntimeError(result.error or "Dynamic scraping failed")
            
            # DynamicScraper._extract_auto returns list of dicts with 'text' for paragraphs
            texts: List[str] = []
            if isinstance(result.data, list):
                for row in result.data:
                    if isinstance(row, dict) and 'text' in row:
                        texts.append(str(row['text']))
            
            task_text = "\n".join(texts) if texts else ""
            
            logger.info(f"✓ Got {len(texts)} text blocks via DynamicScraper")
            
            # Best-effort raw_content: you could extend DynamicScraper to return page.content()
            return {
                'task_description': task_text,
                'raw_content': task_text[:5000],  # at least something readable
            }
        finally:
            await scraper.cleanup()

    # ======================================================================
    # BASIC EXTRACTION (NO LLM)
    # ======================================================================

    async def _extract_basic_content(self, response: httpx.Response, content_type: str) -> str:
        """Fast, no-JS extraction for instruction pages."""
        if content_type == 'json':
            try:
                data = response.json()
                for field in ['task', 'description', 'question', 'content', 'text']:
                    if isinstance(data, dict) and field in data:
                        return str(data[field])
                return json.dumps(data)
            except Exception:
                return response.text
        
        if content_type == 'html':
            try:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                for script in soup(['script', 'style', 'nav', 'header', 'footer']):
                    script.decompose()
                text = soup.get_text(strip=True, separator=' ')
                return text
            except Exception as e:
                logger.error(f"HTML basic extraction failed: {e}")
                return response.text
        
        return response.text

    def _detect_content_type(self, response: httpx.Response) -> str:
        ct = response.headers.get('content-type', '').lower()
        if 'application/json' in ct:
            return 'json'
        if 'text/html' in ct or '<html' in response.text.lower()[:200]:
            return 'html'
        return 'text'

    def _is_valid_url(self, url: str) -> bool:
        try:
            r = urlparse(url)
            return r.scheme in ('http', 'https') and bool(r.netloc)
        except Exception:
            return False

    # ======================================================================
    # LLM ANALYSIS
    # ======================================================================

    async def _analyze_content_with_llm(
        self,
        task_description: str,
        raw_content: str,
        url: str,
        base_url: str
    ):
        """Unified LLM analysis."""
        logger.info("🤖 Running unified LLM analysis...")
        
        url_pattern = r'https?://[^\s<>"\']+(?:/[^\s<>"\']*)?'
        all_urls = re.findall(url_pattern, task_description + raw_content[:1000])
        all_urls = list({u.rstrip('.,;:)') for u in all_urls})
        
        prompt = AnalysisPrompts.unified_content_analysis_prompt(
            task_description=task_description[:2000],
            found_urls=all_urls,
            current_url=url,
            base_url=base_url
        )
        
        from app.orchestrator.models import UnifiedTaskAnalysis
        
        try:
            analysis: UnifiedTaskAnalysis = await self.llm_client.run_agent(
                self._content_analyzer_agent,
                prompt
            )
            return analysis
        except Exception as e:
            logger.error(f"❌ LLM analysis failed: {e}", exc_info=True)
            return self._fallback_analysis(task_description, all_urls, url, base_url)

    def _fallback_analysis(
        self,
        task_description: str,
        all_urls: List[str],
        url: str,
        base_url: str
    ):
        """Very simple fallback if LLM fails."""
        from app.orchestrator.models import UnifiedTaskAnalysis, InstructionStep
        
        logger.warning("⚠️ Using fallback pattern-based analysis")
        
        is_redirect = False
        submission_url = None
        
        for pattern in [r'POST\s+(?:to\s+)?([^\s<>"\']+)', r'submit\s+(?:to\s+)?([^\s<>"\']+)']:
            m = re.search(pattern, task_description, re.IGNORECASE)
            if m:
                submission_url = m.group(1).rstrip('.,;:)')
                break
        
        sentences = re.split(r'[.;\n]', task_description)
        instructions = []
        step = 1
        for s in sentences:
            s = s.strip()
            if len(s) > 5:
                instructions.append(InstructionStep(
                    step_number=step,
                    action='unknown',
                    description=s,
                    target=None,
                    dependencies=[]
                ))
                step += 1
        
        return UnifiedTaskAnalysis(
            is_redirect=is_redirect,
            question_url=None,
            redirect_reasoning="Fallback: no redirect detection",
            submission_url=submission_url,
            submission_url_is_relative=submission_url.startswith('/') if submission_url else False,
            submission_reasoning="Fallback: simple regex match",
            instructions=instructions,
            overall_goal="Unknown (fallback)",
            complexity="unknown",
            confidence=0.3
        )

    def _format_instructions(self, steps) -> List[Dict[str, Any]]:
        return [
            {
                'step': s.step_number,
                'action': s.action,
                'text': s.description,
                'target': s.target,
                'dependencies': s.dependencies,
            }
            for s in steps
        ]
