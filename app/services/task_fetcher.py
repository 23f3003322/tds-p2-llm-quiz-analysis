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
from app.services.analyser import QuestionAnalyzer
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
        self.question_analyzer = QuestionAnalyzer(self.llm_client)
        
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
        print(content)
        logger.debug(f"Task description length after fetch: {len(content['task_description'])}")
        
        file_links = content['question_metadata'].get('file_links', [])

        if file_links:
        # Download files to disk
            downloaded_files = await self._download_files(
                file_links,
                content['base_url'],
                "23f3003322@ds.study.iitm.ac.in"
            )
            content['downloaded_files'] = downloaded_files 
        else:
            content['downloaded_files'] = []

        # Step 2: Unified LLM analysis
        logger.info("🔍 Analyzing question...")
        if not getattr(self.question_analyzer, "_analyzer_agent", None):
            await self.question_analyzer.initialize()

        analysis = await self.question_analyzer.analyze_question(
            question_metadata=content["question_metadata"],
            base_url=base_url,
            user_email="23f3003322@ds.study.iitm.ac.in",
            downloaded_files=content["downloaded_files"]
        )
        result = {
            'analysis': analysis,
            'question_metadata': content['question_metadata'],
            'base_url':base_url,
            'user_email':"23f3003322@ds.study.iitm.ac.in",
            'downloaded_files':content["downloaded_files"]

        }

        return result
        # analysis = await self._analyze_content_with_llm(
        #     task_description=content['task_description'],
        #     raw_content=content['raw_content'],
        #     url=url,
        #     base_url=base_url
        # )
        
        # # Merge content + analysis
        # result = {
        #     **content,
        #     'is_redirect': analysis.is_redirect,
        #     'question_url': analysis.question_url,
        #     'submission_url': analysis.submission_url,
        #     'instructions': self._format_instructions(analysis.instructions),
        #     'overall_goal': analysis.overall_goal,
        #     'complexity': analysis.complexity,
        #     'llm_analysis': {
        #         'redirect_reasoning': analysis.redirect_reasoning,
        #         'submission_reasoning': analysis.submission_reasoning,
        #         'confidence': analysis.confidence,
        #     }
        # }
        
        # # Resolve relative submission URL if needed
        # if analysis.submission_url and analysis.submission_url_is_relative:
        #     absolute = str(httpx.URL(base_url).join(analysis.submission_url))
        #     logger.info(f"✓ Resolved relative submission URL: {analysis.submission_url} → {absolute}")
        #     result['submission_url'] = absolute
        
        # # Resolve relative question URL if needed
        # if analysis.question_url and analysis.question_url.startswith('/'):
        #     absolute_q = str(httpx.URL(base_url).join(analysis.question_url))
        #     logger.info(f"✓ Resolved relative question URL: {analysis.question_url} → {absolute_q}")
        #     result['question_url'] = absolute_q
        
        # logger.info("✅ Analysis complete:")
        # logger.info(f"   Is Redirect: {result['is_redirect']}")
        # logger.info(f"   Submission URL: {result['submission_url']}")
        # logger.info(f"   Instructions: {len(result['instructions'])} steps")
        # logger.info(f"   Complexity: {result['complexity']}")
        
        # return result

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
        
        from urllib.parse import urlparse

        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        try:
            response = await self._fetch_url(url)
            content_type = self._detect_content_type(response)
            html_content = response.text  # ← This is html_content
            html_content = html_content.replace(
                '<span class="origin"></span>', 
             base_url
            )
            # Basic extraction
            task_description = await self._extract_basic_content_from_html(html_content, content_type)
            raw_content = response.text[:5000]
            
            metadata = self._parse_question_metadata(html_content)
            # Heuristic: if nothing useful, try dynamic scraper
            if self._looks_js_only(task_description, raw_content):
                logger.warning("⚠️ Content looks JS-only/empty. Falling back to DynamicScraper for instructions.")
                dyn = await self._fetch_with_dynamic_scraper(url)
                task_description = dyn['task_description']
                raw_content = dyn['raw_content']
                metadata = dyn['question_metadata']

            return {
                    'task_description': task_description,
                    'raw_content': raw_content,
        'content_type': content_type,
        'url': url,
        'base_url': base_url,
        'question_metadata': metadata,  # ✓ ADDED
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
        from urllib.parse import urlparse
    
        # Extract base URL
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        scraper = DynamicScraper(use_pool=True)
        await scraper.initialize()
        try:
            # Auto-extract text blocks
            result = await scraper.scrape_url(url)
            
            if not result.success:
                raise RuntimeError(result.error or "Dynamic scraping failed")
            
            rendered_html = result.raw_html if hasattr(result, 'raw_html') else None
            if rendered_html:
                rendered_html = rendered_html.replace(
                '<span class="origin"></span>', 
                base_url
            )
                
            question_metadata = None
            if rendered_html:
                soup = BeautifulSoup(rendered_html, 'html.parser')
                question_metadata = self._parse_question_metadata_from_soup(soup)
            file_links = []
            if rendered_html:
                soup = BeautifulSoup(rendered_html, 'html.parser')
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if href.startswith('/project2/'):
                        file_links.append({
                            'href': href,
                            'text': a.get_text(strip=True)
                        })

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
            'raw_content': rendered_html if rendered_html else task_text[:5000],
            'base_url': base_url,
            'question_metadata': question_metadata,  # NEW
            }
        finally:
            await scraper.cleanup()

    # ======================================================================
    # BASIC EXTRACTION (NO LLM)
    # ======================================================================

    async def _extract_basic_content_from_html(
        self, 
        html_content: str,  # ← Changed from response
        content_type: str
    ) -> str:
        """
        Fast extraction from HTML string (no JS execution).
        """
        if content_type == 'json':
            try:
                data = json.loads(html_content)
                for field in ['task', 'description', 'question', 'content', 'text']:
                    if isinstance(data, dict) and field in data:
                        return str(data[field])
                return json.dumps(data)
            except Exception:
                return html_content
        
        if content_type == 'html':
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Remove scripts (but origin already replaced before this)
                for script in soup(['script', 'style', 'nav', 'header', 'footer']):
                    script.decompose()
                
                text = soup.get_text(strip=True, separator=' ')
                return text
            except Exception as e:
                logger.error(f"HTML basic extraction failed: {e}")
                return html_content
        
        return html_content

    def _parse_question_metadata(self, html: str) -> Dict[str, Any]:
        """
        Extract structured metadata from question HTML.
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        metadata = {
            'title': None,
            'heading': None,
            'difficulty': None,
            'is_personalized': False,
            'instructions': [],
            'file_links': []
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.text.strip()
        
        # Extract heading
        h1_tag = soup.find('h1')
        if h1_tag:
            metadata['heading'] = h1_tag.text.strip()
        
        # Extract difficulty and personalization
        for p in soup.find_all('p'):
            text = p.get_text()
            
            # Difficulty: "Difficulty: 1 (next URL revealed even if wrong)"
            if 'Difficulty:' in text:
                import re
                match = re.search(r'Difficulty:\s*(\d+)', text)
                if match:
                    metadata['difficulty'] = int(match.group(1))
            
            # Personalization: "Personalized: Yes" or "Personalized: No"
            if 'Personalized:' in text:
                metadata['is_personalized'] = 'Yes' in text
        
        # Extract ordered instructions
        ol_tag = soup.find('ol')
        if ol_tag:
            for li in ol_tag.find_all('li', recursive=False):
                metadata['instructions'].append(li.get_text(strip=True))
        
        # Extract file links
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('/project2/'):
                metadata['file_links'].append({
                    'href': href,
                    'text': a.get_text(strip=True)
                })
        
        return metadata

    def _parse_question_metadata_from_soup(self, soup) -> Dict[str, Any]:
        """
        Extract structured metadata from BeautifulSoup object.
        Helper method for both httpx and dynamic scraper paths.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            Dict with title, difficulty, personalization, instructions, file_links
        """
        metadata = {
            'title': None,
            'heading': None,
            'difficulty': None,
            'is_personalized': False,
            'instructions': [],
            'file_links': []
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.text.strip()
        
        # Extract heading
        h1_tag = soup.find('h1')
        if h1_tag:
            metadata['heading'] = h1_tag.text.strip()
        
        # Extract difficulty and personalization from paragraphs
        for p in soup.find_all('p'):
            text = p.get_text()
            
            # Parse difficulty: "Difficulty: 1 (next URL revealed even if wrong)"
            if 'Difficulty:' in text or 'difficulty:' in text.lower():
                import re
                match = re.search(r'[Dd]ifficulty:\s*(\d+)', text)
                if match:
                    metadata['difficulty'] = int(match.group(1))
                    logger.debug(f"Parsed difficulty: {metadata['difficulty']}")
            
            # Parse personalization: "Personalized: Yes" or "Personalized: No"
            if 'Personalized:' in text or 'personalized:' in text.lower():
                metadata['is_personalized'] = 'yes' in text.lower()
                logger.debug(f"Parsed personalization: {metadata['is_personalized']}")
        
        # Extract ordered instructions from <ol> tag
        ol_tag = soup.find('ol')
        if ol_tag:
            for li in ol_tag.find_all('li', recursive=False):
                instruction_text = li.get_text(separator=' ', strip=True)
                metadata['instructions'].append(instruction_text)
            logger.debug(f"Parsed {len(metadata['instructions'])} instructions")
        
        # Extract file links from <a> tags
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Look for project files
            if href.startswith('/project2/') or '/project2/' in href:
                metadata['file_links'].append({
                    'href': href,
                    'text': a.get_text(strip=True)
                })
        
        if metadata['file_links']:
            logger.debug(f"Found {len(metadata['file_links'])} file links")
        
        return metadata


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
            return 
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
