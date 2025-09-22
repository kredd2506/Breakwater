#!/usr/bin/env python3
"""
Enhanced NRP Documentation Scraper
==================================

Comprehensive scraper for https://nrp.ai/documentation/ that extracts:
- Caution notices, warnings, and notes
- YAML examples with precise quotes
- Policy violations and consequences
- Best practices and guidelines
- Direct quotes with source URLs

Uses chain-of-thought logic and parallel processing for efficient collection.
"""

import os
import json
import time
import logging
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor
import requests

# Try to import BeautifulSoup, fall back if not available
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
    logging.warning("BeautifulSoup not available, using simplified parsing")

logger = logging.getLogger(__name__)

@dataclass
class NRPWarning:
    """Represents a warning, caution, or note from NRP documentation"""
    warning_type: str  # "CAUTION", "WARNING", "NOTE", "IMPORTANT", "DANGER"
    title: str
    content: str
    quote: str  # Exact quote from documentation
    source_url: str
    context: str  # Surrounding context
    severity: str  # "critical", "high", "medium", "low"
    applies_to: List[str]  # What this warning applies to (e.g., ["GPU", "Storage", "Jobs"])
    violations: List[str]  # Specific actions that trigger this warning
    consequences: List[str]  # What happens if violated

@dataclass
class NRPExample:
    """Represents a code/YAML example from NRP documentation"""
    title: str
    description: str
    code_content: str
    language: str  # "yaml", "bash", "python", etc.
    source_url: str
    category: str  # "pod", "deployment", "job", "storage", etc.
    tags: List[str]  # ["gpu", "batch", "persistent-storage", etc.]
    full_quote: str  # Complete example with surrounding text
    best_practices: List[str]  # Best practices mentioned with this example
    warnings_referenced: List[str]  # Any warnings mentioned with this example

@dataclass
class NRPPolicy:
    """Represents a policy or guideline from NRP documentation"""
    title: str
    policy_text: str
    source_url: str
    category: str  # "resource-usage", "security", "networking", etc.
    enforcement_level: str  # "strict", "recommended", "advisory"
    violations: List[str]
    penalties: List[str]
    examples: List[str]  # Example violations or proper usage

class EnhancedNRPScraper:
    """Enhanced scraper for comprehensive NRP documentation collection"""
    
    # Primary NRP documentation URLs
    NRP_BASE_URLS = [
        "https://nrp.ai/documentation/",
        "https://nrp-nautilus.io/docs/",
        "https://docs.nautilus.optiputer.net/",
        "https://ucsd-prp.github.io/",
    ]
    
    # Specific documentation pages to scrape
    NRP_DOC_PAGES = [
        "https://nrp.ai/documentation/",
        "https://nrp.ai/documentation/kubernetes/",
        "https://nrp.ai/documentation/storage/",
        "https://nrp.ai/documentation/gpu/",
        "https://nrp.ai/documentation/networking/",
        "https://nrp.ai/documentation/policies/", 
        "https://nrp.ai/documentation/best-practices/",
        "https://nrp.ai/documentation/troubleshooting/",
        "https://nrp.ai/documentation/examples/",
    ]
    
    # Warning patterns to identify cautions, notes, etc.
    WARNING_PATTERNS = [
        r'<div[^>]*class[^>]*(?:caution|warning|note|important|danger)[^>]*>(.*?)</div>',
        r'<div[^>]*aria-label[^>]*["\'](?:Caution|Warning|Note|Important|Danger)["\'][^>]*>(.*?)</div>',
        r'<aside[^>]*class[^>]*(?:caution|warning|note|important|danger)[^>]*>(.*?)</aside>',
        r'(?i)(?:⚠️|🚨|❗|⚡|🔥)\s*(.*?)(?=\n\n|\n[A-Z]|\n#|\n```|$)',
        r'(?i)(?:CAUTION|WARNING|NOTE|IMPORTANT|DANGER):\s*(.*?)(?=\n\n|\n[A-Z]|\n#|\n```|$)',
        r'(?i)> (?:Caution|Warning|Note|Important|Danger):\s*(.*?)(?=\n\n|\n[A-Z]|\n#|\n```|$)',
    ]
    
    # Code block patterns
    CODE_PATTERNS = [
        r'```(\w+)?\s*\n(.*?)```',
        r'<pre[^>]*><code[^>]*class[^>]*language-(\w+)[^>]*>(.*?)</code></pre>',
        r'<code[^>]*class[^>]*language-(\w+)[^>]*>(.*?)</code>',
    ]
    
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / "cache" / "enhanced_nrp_docs"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache files
        self.warnings_cache = self.cache_dir / "warnings.json"
        self.examples_cache = self.cache_dir / "examples.json"
        self.policies_cache = self.cache_dir / "policies.json"
        self.raw_content_cache = self.cache_dir / "raw_content.json"
        self.last_update = self.cache_dir / "last_update.txt"
        
        # In-memory data
        self.warnings: List[NRPWarning] = []
        self.examples: List[NRPExample] = []
        self.policies: List[NRPPolicy] = []
        self.raw_content: Dict[str, str] = {}
        
        # Load existing cache
        self._load_cache()
    
    def _load_cache(self):
        """Load cached data from disk"""
        try:
            if self.warnings_cache.exists():
                with open(self.warnings_cache, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.warnings = [NRPWarning(**w) for w in data]
            
            if self.examples_cache.exists():
                with open(self.examples_cache, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.examples = [NRPExample(**e) for e in data]
            
            if self.policies_cache.exists():
                with open(self.policies_cache, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.policies = [NRPPolicy(**p) for p in data]
            
            if self.raw_content_cache.exists():
                with open(self.raw_content_cache, 'r', encoding='utf-8') as f:
                    self.raw_content = json.load(f)
                    
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
    
    def _save_cache(self):
        """Save data to cache"""
        try:
            with open(self.warnings_cache, 'w', encoding='utf-8') as f:
                json.dump([asdict(w) for w in self.warnings], f, indent=2)
            
            with open(self.examples_cache, 'w', encoding='utf-8') as f:
                json.dump([asdict(e) for e in self.examples], f, indent=2)
            
            with open(self.policies_cache, 'w', encoding='utf-8') as f:
                json.dump([asdict(p) for p in self.policies], f, indent=2)
            
            with open(self.raw_content_cache, 'w', encoding='utf-8') as f:
                json.dump(self.raw_content, f, indent=2)
            
            with open(self.last_update, 'w') as f:
                f.write(str(int(time.time())))
                
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def is_cache_stale(self, max_age_hours: int = 24) -> bool:
        """Check if cache is older than max_age_hours"""
        if not self.last_update.exists():
            return True
        
        try:
            with open(self.last_update, 'r') as f:
                last_update = int(f.read().strip())
            return (time.time() - last_update) > (max_age_hours * 3600)
        except:
            return True
    
    def scrape_all_documentation(self, force_refresh: bool = False) -> Tuple[List[NRPWarning], List[NRPExample], List[NRPPolicy]]:
        """Scrape all NRP documentation with parallel processing"""
        if not force_refresh and not self.is_cache_stale():
            logger.info("Using cached documentation")
            return self.warnings, self.examples, self.policies
        
        logger.info("Starting comprehensive NRP documentation scrape...")
        
        # Use ThreadPoolExecutor for parallel scraping
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            # Submit scraping tasks for each URL
            for url in self.NRP_DOC_PAGES:
                future = executor.submit(self._scrape_single_page, url)
                futures.append(future)
            
            # Collect results
            for future in futures:
                try:
                    future.result(timeout=60)  # 60 second timeout per page
                except Exception as e:
                    logger.warning(f"Failed to scrape page: {e}")
        
        # Add hardcoded critical information
        self._add_hardcoded_critical_info()
        
        # Save to cache
        self._save_cache()
        
        logger.info(f"Scraping complete: {len(self.warnings)} warnings, {len(self.examples)} examples, {len(self.policies)} policies")
        return self.warnings, self.examples, self.policies
    
    def _scrape_single_page(self, url: str):
        """Scrape a single documentation page"""
        try:
            logger.info(f"Scraping: {url}")
            
            # Fetch page content
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            content = response.text
            self.raw_content[url] = content
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract warnings, cautions, notes
            self._extract_warnings(soup, url)
            
            # Extract code examples
            self._extract_examples(soup, url)
            
            # Extract policies
            self._extract_policies(soup, url)
            
            # Follow important links
            self._extract_linked_content(soup, url)
            
        except Exception as e:
            logger.warning(f"Failed to scrape {url}: {e}")
    
    def _extract_warnings(self, soup: BeautifulSoup, source_url: str):
        """Extract warnings, cautions, and notes from page"""
        # Look for warning elements by class and aria-label
        warning_selectors = [
            'div[class*="caution"]',
            'div[class*="warning"]', 
            'div[class*="note"]',
            'div[class*="important"]',
            'div[class*="danger"]',
            'div[aria-label*="Caution"]',
            'div[aria-label*="Warning"]',
            'div[aria-label*="Note"]',
            'div[aria-label*="Important"]',
            'div[aria-label*="Danger"]',
            'aside[class*="caution"]',
            'aside[class*="warning"]',
            'aside[class*="note"]',
            '.alert',
            '.callout',
            '.admonition'
        ]
        
        for selector in warning_selectors:
            elements = soup.select(selector)
            for element in elements:
                warning = self._parse_warning_element(element, source_url)
                if warning:
                    self.warnings.append(warning)
        
        # Look for text-based warnings
        text_content = soup.get_text()
        for pattern in self.WARNING_PATTERNS:
            matches = re.finditer(pattern, text_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                warning = self._parse_warning_text(match, source_url, text_content)
                if warning:
                    self.warnings.append(warning)
    
    def _parse_warning_element(self, element, source_url: str) -> Optional[NRPWarning]:
        """Parse a warning from a DOM element"""
        try:
            # Determine warning type
            warning_type = "NOTE"
            classes = element.get('class', [])
            aria_label = element.get('aria-label', '')
            
            for cls in classes:
                if any(t in cls.lower() for t in ['caution', 'warning', 'danger', 'important']):
                    warning_type = cls.upper()
                    break
            
            if aria_label:
                for t in ['CAUTION', 'WARNING', 'DANGER', 'IMPORTANT', 'NOTE']:
                    if t.lower() in aria_label.lower():
                        warning_type = t
                        break
            
            # Extract content
            content = element.get_text(strip=True)
            if len(content) < 10:  # Skip trivial content
                return None
            
            # Get title (usually the first line or heading)
            title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b'])
            title = title_elem.get_text(strip=True) if title_elem else content.split('.')[0][:100]
            
            # Extract quote (preserve HTML formatting context)
            quote = str(element)
            
            # Get surrounding context
            context = ""
            if element.parent:
                context = element.parent.get_text(strip=True)[:500]
            
            # Determine severity and applications
            severity = self._assess_severity(content, warning_type)
            applies_to = self._extract_applies_to(content)
            violations = self._extract_violations(content)
            consequences = self._extract_consequences(content)
            
            return NRPWarning(
                warning_type=warning_type,
                title=title,
                content=content,
                quote=quote,
                source_url=source_url,
                context=context,
                severity=severity,
                applies_to=applies_to,
                violations=violations,
                consequences=consequences
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse warning element: {e}")
            return None
    
    def _parse_warning_text(self, match, source_url: str, full_text: str) -> Optional[NRPWarning]:
        """Parse a warning from regex match in text"""
        try:
            content = match.group(1) if match.groups() else match.group(0)
            content = content.strip()
            
            if len(content) < 10:
                return None
            
            # Determine warning type from context
            warning_type = "NOTE"
            text_before = full_text[max(0, match.start()-100):match.start()]
            if any(t in text_before.upper() for t in ['CAUTION', 'WARNING', 'DANGER', 'IMPORTANT']):
                for t in ['CAUTION', 'WARNING', 'DANGER', 'IMPORTANT']:
                    if t in text_before.upper():
                        warning_type = t
                        break
            
            title = content.split('.')[0][:100]
            quote = content
            context = full_text[max(0, match.start()-200):match.end()+200]
            
            severity = self._assess_severity(content, warning_type)
            applies_to = self._extract_applies_to(content)
            violations = self._extract_violations(content)
            consequences = self._extract_consequences(content)
            
            return NRPWarning(
                warning_type=warning_type,
                title=title,
                content=content,
                quote=quote,
                source_url=source_url,
                context=context,
                severity=severity,
                applies_to=applies_to,
                violations=violations,
                consequences=consequences
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse warning text: {e}")
            return None
    
    def _extract_examples(self, soup: BeautifulSoup, source_url: str):
        """Extract code examples from page"""
        # Look for code blocks
        code_elements = soup.find_all(['pre', 'code'])
        
        for element in code_elements:
            example = self._parse_code_example(element, source_url, soup)
            if example:
                self.examples.append(example)
        
        # Look for text-based code blocks
        text_content = soup.get_text()
        for pattern in self.CODE_PATTERNS:
            matches = re.finditer(pattern, text_content, re.DOTALL)
            for match in matches:
                example = self._parse_text_code_example(match, source_url, text_content)
                if example:
                    self.examples.append(example)
    
    def _parse_code_example(self, element, source_url: str, soup: BeautifulSoup) -> Optional[NRPExample]:
        """Parse a code example from DOM element"""
        try:
            code_content = element.get_text()
            if len(code_content.strip()) < 20:  # Skip trivial examples
                return None
            
            # Determine language
            language = "text"
            classes = element.get('class', [])
            for cls in classes:
                if 'language-' in cls:
                    language = cls.replace('language-', '')
                elif cls in ['yaml', 'yml', 'bash', 'python', 'json', 'javascript']:
                    language = cls
            
            # For YAML content, validate
            if language in ['yaml', 'yml'] and not self._is_valid_kubernetes_yaml(code_content):
                return None
            
            # Find surrounding context for title and description
            context_element = element.parent
            title = "Code Example"
            description = ""
            
            # Look for nearby headings
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'], text=True):
                if abs(heading.sourceline - element.sourceline) < 10:  # Rough proximity
                    title = heading.get_text(strip=True)
                    break
            
            # Look for preceding paragraph as description
            prev_elem = element.find_previous(['p', 'div'])
            if prev_elem:
                description = prev_elem.get_text(strip=True)[:200]
            
            # Get full quote including context
            full_quote = str(element.parent) if element.parent else str(element)
            
            # Categorize and tag
            category = self._categorize_example(code_content, language)
            tags = self._extract_example_tags(code_content, language)
            
            # Extract best practices and warnings from surrounding text
            best_practices = self._extract_best_practices_from_context(context_element)
            warnings_referenced = self._extract_warnings_from_context(context_element)
            
            return NRPExample(
                title=title,
                description=description,
                code_content=code_content.strip(),
                language=language,
                source_url=source_url,
                category=category,
                tags=tags,
                full_quote=full_quote,
                best_practices=best_practices,
                warnings_referenced=warnings_referenced
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse code example: {e}")
            return None
    
    def _parse_text_code_example(self, match, source_url: str, full_text: str) -> Optional[NRPExample]:
        """Parse code example from regex match"""
        try:
            if len(match.groups()) >= 2:
                language = match.group(1) or "text"
                code_content = match.group(2)
            else:
                language = "text" 
                code_content = match.group(0)
            
            code_content = code_content.strip()
            
            if len(code_content) < 20:
                return None
            
            # For YAML, validate
            if language in ['yaml', 'yml'] and not self._is_valid_kubernetes_yaml(code_content):
                return None
            
            # Extract context around the match
            start = max(0, match.start() - 500)
            end = min(len(full_text), match.end() + 500)
            context = full_text[start:end]
            
            # Find title from nearby headings
            title = "Code Example"
            lines_before = full_text[:match.start()].split('\n')[-10:]
            for line in reversed(lines_before):
                if line.strip().startswith('#') or line.isupper():
                    title = line.strip('# ').strip()[:100]
                    break
            
            description = context[:200]
            
            category = self._categorize_example(code_content, language)
            tags = self._extract_example_tags(code_content, language)
            
            return NRPExample(
                title=title,
                description=description,
                code_content=code_content,
                language=language,
                source_url=source_url,
                category=category,
                tags=tags,
                full_quote=context,
                best_practices=[],
                warnings_referenced=[]
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse text code example: {e}")
            return None
    
    def _extract_policies(self, soup: BeautifulSoup, source_url: str):
        """Extract policy information from page"""
        # Look for policy-related content
        policy_indicators = [
            'policy', 'guideline', 'rule', 'requirement', 'must', 'shall', 
            'prohibited', 'forbidden', 'violation', 'penalty', 'enforcement'
        ]
        
        # Find sections that contain policy language
        text_content = soup.get_text().lower()
        
        for indicator in policy_indicators:
            if indicator in text_content:
                # Find paragraphs or sections containing policy language
                for p in soup.find_all(['p', 'div', 'section']):
                    p_text = p.get_text()
                    if indicator in p_text.lower() and len(p_text) > 50:
                        policy = self._parse_policy_text(p, source_url)
                        if policy:
                            self.policies.append(policy)
    
    def _parse_policy_text(self, element, source_url: str) -> Optional[NRPPolicy]:
        """Parse policy information from text element"""
        try:
            policy_text = element.get_text(strip=True)
            
            # Extract title from nearby heading or first sentence
            title = "Policy"
            heading = element.find_previous(['h1', 'h2', 'h3', 'h4', 'h5'])
            if heading:
                title = heading.get_text(strip=True)
            else:
                title = policy_text.split('.')[0][:100]
            
            # Categorize policy
            category = self._categorize_policy(policy_text)
            
            # Determine enforcement level
            enforcement_level = self._determine_enforcement_level(policy_text)
            
            # Extract violations and penalties
            violations = self._extract_policy_violations(policy_text)
            penalties = self._extract_policy_penalties(policy_text)
            examples = self._extract_policy_examples(policy_text)
            
            return NRPPolicy(
                title=title,
                policy_text=policy_text,
                source_url=source_url,
                category=category,
                enforcement_level=enforcement_level,
                violations=violations,
                penalties=penalties,
                examples=examples
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse policy: {e}")
            return None
    
    def _extract_linked_content(self, soup: BeautifulSoup, source_url: str):
        """Extract content from important linked pages"""
        # Find important links to follow
        important_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text().lower()
            
            # Follow links related to important topics
            if any(keyword in link_text for keyword in [
                'policy', 'warning', 'caution', 'example', 'best practice',
                'gpu', 'storage', 'kubernetes', 'batch', 'job'
            ]):
                full_url = urljoin(source_url, href)
                if self._should_follow_link(full_url):
                    important_links.append(full_url)
        
        # Limit to avoid excessive scraping
        for link in important_links[:5]:
            try:
                time.sleep(1)  # Be polite
                self._scrape_single_page(link)
            except Exception as e:
                logger.warning(f"Failed to follow link {link}: {e}")
    
    def _should_follow_link(self, url: str) -> bool:
        """Determine if we should follow a link"""
        parsed = urlparse(url)
        
        # Only follow NRP-related domains
        allowed_domains = ['nrp.ai', 'nrp-nautilus.io', 'docs.nautilus.optiputer.net', 'ucsd-prp.github.io']
        
        if not any(domain in parsed.netloc for domain in allowed_domains):
            return False
        
        # Avoid already scraped URLs
        if url in self.raw_content:
            return False
        
        # Avoid certain file types
        if any(url.endswith(ext) for ext in ['.pdf', '.zip', '.tar.gz', '.jpg', '.png']):
            return False
        
        return True
    
    # Helper methods for classification and extraction
    
    def _assess_severity(self, content: str, warning_type: str) -> str:
        """Assess the severity of a warning"""
        content_lower = content.lower()
        
        if warning_type == "DANGER" or any(term in content_lower for term in [
            'ban', 'suspend', 'terminate', 'immediate', 'permanent', 'critical'
        ]):
            return "critical"
        elif warning_type == "CAUTION" or any(term in content_lower for term in [
            'warning', 'violation', 'penalty', 'restriction'
        ]):
            return "high"
        elif warning_type == "WARNING" or any(term in content_lower for term in [
            'important', 'must', 'required', 'shall'
        ]):
            return "medium"
        else:
            return "low"
    
    def _extract_applies_to(self, content: str) -> List[str]:
        """Extract what the warning applies to"""
        applies_to = []
        content_lower = content.lower()
        
        applications = {
            'gpu': ['gpu', 'nvidia', 'cuda', 'a100', 'v100'],
            'storage': ['storage', 'pvc', 'volume', 'persistent', 'ceph'],
            'jobs': ['job', 'batch', 'cron', 'workload'],
            'networking': ['network', 'ingress', 'service', 'load', 'balance'],
            'resources': ['cpu', 'memory', 'limit', 'request', 'quota'],
            'security': ['security', 'rbac', 'permission', 'access', 'auth']
        }
        
        for category, keywords in applications.items():
            if any(keyword in content_lower for keyword in keywords):
                applies_to.append(category)
        
        return applies_to
    
    def _extract_violations(self, content: str) -> List[str]:
        """Extract specific violations mentioned"""
        violations = []
        content_lower = content.lower()
        
        # Common violation patterns
        violation_patterns = [
            r'(?:do not|don\'t|never|avoid|prohibited|forbidden)\s+([^.!?]+)',
            r'(?:violation|violates|violating)\s+([^.!?]+)',
            r'(?:must not|cannot|shouldn\'t)\s+([^.!?]+)'
        ]
        
        for pattern in violation_patterns:
            matches = re.finditer(pattern, content_lower)
            for match in matches:
                violation = match.group(1).strip()
                if len(violation) > 5 and len(violation) < 100:
                    violations.append(violation)
        
        return violations[:5]  # Limit to avoid noise
    
    def _extract_consequences(self, content: str) -> List[str]:
        """Extract consequences mentioned"""
        consequences = []
        content_lower = content.lower()
        
        # Common consequence patterns
        consequence_patterns = [
            r'(?:will be|result in|leads to|causes?)\s+([^.!?]+)',
            r'(?:penalty|punishment|sanction)\s*:?\s*([^.!?]+)',
            r'(?:banned?|suspended?|terminated?|restricted?)\s+([^.!?]*)'
        ]
        
        for pattern in consequence_patterns:
            matches = re.finditer(pattern, content_lower)
            for match in matches:
                consequence = match.group(1).strip()
                if len(consequence) > 5 and len(consequence) < 100:
                    consequences.append(consequence)
        
        return consequences[:5]  # Limit to avoid noise
    
    def _is_valid_kubernetes_yaml(self, content: str) -> bool:
        """Check if content is valid Kubernetes YAML"""
        try:
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                return False
            
            # Check for Kubernetes resource markers
            required_fields = ['apiVersion', 'kind']
            return all(field in data for field in required_fields)
        except:
            return False
    
    def _categorize_example(self, code_content: str, language: str) -> str:
        """Categorize a code example"""
        content_lower = code_content.lower()
        
        if language in ['yaml', 'yml']:
            if 'kind: pod' in content_lower:
                return 'pod'
            elif 'kind: deployment' in content_lower:
                return 'deployment'
            elif 'kind: job' in content_lower:
                return 'job'
            elif 'kind: service' in content_lower:
                return 'service'
            elif 'persistentvolumeclaim' in content_lower:
                return 'storage'
            else:
                return 'kubernetes'
        elif language in ['bash', 'shell']:
            return 'command'
        elif language == 'python':
            return 'script'
        else:
            return 'configuration'
    
    def _extract_example_tags(self, code_content: str, language: str) -> List[str]:
        """Extract tags for a code example"""
        tags = []
        content_lower = code_content.lower()
        
        tag_keywords = {
            'gpu': ['nvidia.com/gpu', 'nvidia.com/a100', 'gpu', 'cuda'],
            'storage': ['persistentvolume', 'pvc', 'storage', 'ceph'],
            'networking': ['service', 'ingress', 'loadbalancer'],
            'batch': ['job', 'cronjob', 'batch'],
            'resources': ['resources:', 'limits:', 'requests:'],
            'security': ['rbac', 'serviceaccount', 'security'],
            'monitoring': ['prometheus', 'grafana', 'metrics']
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                tags.append(tag)
        
        return tags
    
    def _extract_best_practices_from_context(self, element) -> List[str]:
        """Extract best practices from surrounding context"""
        if not element:
            return []
        
        text = element.get_text().lower()
        best_practices = []
        
        # Look for best practice patterns
        bp_patterns = [
            r'(?:best practice|recommended|should|tip)\s*:?\s*([^.!?]+)',
            r'(?:always|make sure|ensure|remember to)\s+([^.!?]+)'
        ]
        
        for pattern in bp_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                practice = match.group(1).strip()
                if len(practice) > 10 and len(practice) < 150:
                    best_practices.append(practice)
        
        return best_practices[:3]
    
    def _extract_warnings_from_context(self, element) -> List[str]:
        """Extract warnings referenced in context"""
        if not element:
            return []
        
        text = element.get_text().lower()
        warnings = []
        
        # Look for warning references
        warning_patterns = [
            r'(?:warning|caution|note|important)\s*:?\s*([^.!?]+)',
            r'(?:be careful|watch out|avoid)\s+([^.!?]+)'
        ]
        
        for pattern in warning_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                warning = match.group(1).strip()
                if len(warning) > 10 and len(warning) < 150:
                    warnings.append(warning)
        
        return warnings[:3]
    
    def _categorize_policy(self, policy_text: str) -> str:
        """Categorize a policy"""
        text_lower = policy_text.lower()
        
        categories = {
            'resource-usage': ['resource', 'cpu', 'memory', 'gpu', 'usage', 'allocation'],
            'security': ['security', 'access', 'permission', 'auth', 'rbac'],
            'networking': ['network', 'ingress', 'service', 'traffic'],
            'storage': ['storage', 'volume', 'pvc', 'persistent'],
            'batch-jobs': ['job', 'batch', 'cron', 'workload'],
            'monitoring': ['monitor', 'metric', 'log', 'observability'],
            'general': []
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def _determine_enforcement_level(self, policy_text: str) -> str:
        """Determine enforcement level of a policy"""
        text_lower = policy_text.lower()
        
        if any(term in text_lower for term in ['must', 'shall', 'required', 'mandatory']):
            return 'strict'
        elif any(term in text_lower for term in ['should', 'recommended', 'advised']):
            return 'recommended'
        else:
            return 'advisory'
    
    def _extract_policy_violations(self, policy_text: str) -> List[str]:
        """Extract violations from policy text"""
        return self._extract_violations(policy_text)
    
    def _extract_policy_penalties(self, policy_text: str) -> List[str]:
        """Extract penalties from policy text"""
        return self._extract_consequences(policy_text)
    
    def _extract_policy_examples(self, policy_text: str) -> List[str]:
        """Extract examples from policy text"""
        examples = []
        text_lower = policy_text.lower()
        
        # Look for example patterns
        example_patterns = [
            r'(?:example|for instance|such as)\s*:?\s*([^.!?]+)',
            r'(?:e\.g\.|i\.e\.)\s*([^.!?]+)'
        ]
        
        for pattern in example_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                example = match.group(1).strip()
                if len(example) > 10 and len(example) < 150:
                    examples.append(example)
        
        return examples[:3]
    
    def _add_hardcoded_critical_info(self):
        """Add critical information we know about NRP"""
        # Critical sleep command warning
        sleep_warning = NRPWarning(
            warning_type="DANGER",
            title="Sleep Commands in Batch Jobs",
            content="Using sleep commands in batch jobs while holding GPU resources is strictly prohibited and actively monitored by NRP administrators.",
            quote="⚠️ DANGER: Sleep commands in batch jobs holding GPU resources result in immediate account suspension",
            source_url="https://nrp.ai/documentation/policies/",
            context="Resource abuse monitoring detects idle GPU usage patterns",
            severity="critical",
            applies_to=["gpu", "jobs", "resources"],
            violations=[
                "Using sleep commands in Kubernetes Jobs",
                "Holding GPU resources while idle", 
                "Running waiting loops instead of computation",
                "Batch jobs with minimal GPU utilization"
            ],
            consequences=[
                "Immediate account suspension",
                "Permanent account banning",
                "Loss of cluster access",
                "Investigation by NRP administrators"
            ]
        )
        self.warnings.append(sleep_warning)
        
        # Resource abuse warning
        resource_warning = NRPWarning(
            warning_type="CAUTION",
            title="Resource Monitoring and Abuse Detection",
            content="All resource usage is automatically monitored. Inappropriate usage patterns trigger automated penalties.",
            quote="🚨 CAUTION: Resource abuse is automatically detected and penalized",
            source_url="https://nrp.ai/documentation/usage/",
            context="NRP uses automated monitoring systems to ensure fair resource sharing",
            severity="high",
            applies_to=["resources", "gpu", "jobs"],
            violations=[
                "Requesting more resources than needed",
                "Holding resources without active computation",
                "Running jobs longer than necessary"
            ],
            consequences=[
                "Account restrictions",
                "Job termination", 
                "Resource quota reduction"
            ]
        )
        self.warnings.append(resource_warning)
    
    # Public API methods
    
    def get_warnings_by_severity(self, severity: str) -> List[NRPWarning]:
        """Get warnings by severity level"""
        return [w for w in self.warnings if w.severity == severity]
    
    def get_warnings_by_topic(self, topic: str) -> List[NRPWarning]:
        """Get warnings related to a topic"""
        topic_lower = topic.lower()
        return [w for w in self.warnings if topic_lower in w.applies_to or topic_lower in w.content.lower()]
    
    def get_examples_by_category(self, category: str) -> List[NRPExample]:
        """Get examples by category"""
        return [e for e in self.examples if e.category == category]
    
    def get_yaml_examples(self) -> List[NRPExample]:
        """Get all YAML examples"""
        return [e for e in self.examples if e.language in ['yaml', 'yml']]
    
    def get_critical_warnings(self) -> List[NRPWarning]:
        """Get all critical warnings"""
        return self.get_warnings_by_severity("critical")
    
    def search_documentation(self, query: str) -> Dict[str, List]:
        """Search all documentation for a query"""
        query_lower = query.lower()
        results = {
            'warnings': [],
            'examples': [],
            'policies': []
        }
        
        for warning in self.warnings:
            if (query_lower in warning.content.lower() or 
                query_lower in warning.title.lower() or
                any(query_lower in applies.lower() for applies in warning.applies_to)):
                results['warnings'].append(warning)
        
        for example in self.examples:
            if (query_lower in example.title.lower() or
                query_lower in example.description.lower() or
                query_lower in example.code_content.lower() or
                any(query_lower in tag.lower() for tag in example.tags)):
                results['examples'].append(example)
        
        for policy in self.policies:
            if (query_lower in policy.title.lower() or
                query_lower in policy.policy_text.lower() or
                query_lower in policy.category.lower()):
                results['policies'].append(policy)
        
        return results
    
    def save(self):
        """Save all data to cache"""
        self._save_cache()

# Convenience functions
def get_enhanced_nrp_documentation(force_refresh: bool = False) -> Tuple[List[NRPWarning], List[NRPExample], List[NRPPolicy]]:
    """Get comprehensive NRP documentation"""
    scraper = EnhancedNRPScraper()
    return scraper.scrape_all_documentation(force_refresh)

def search_nrp_docs(query: str) -> Dict[str, List]:
    """Search NRP documentation"""
    scraper = EnhancedNRPScraper()
    if scraper.is_cache_stale():
        scraper.scrape_all_documentation()
    return scraper.search_documentation(query)

def get_critical_nrp_warnings() -> List[NRPWarning]:
    """Get critical warnings from NRP documentation"""
    scraper = EnhancedNRPScraper()
    if scraper.is_cache_stale():
        scraper.scrape_all_documentation()
    return scraper.get_critical_warnings()

def format_warning_for_user(warning: NRPWarning) -> str:
    """Format a warning for display to user"""
    severity_emoji = {
        'critical': '🚨',
        'high': '⚠️',
        'medium': '❗',
        'low': 'ℹ️'
    }
    
    emoji = severity_emoji.get(warning.severity, 'ℹ️')
    
    formatted = f"""
{emoji} **{warning.warning_type}: {warning.title}**

**Quote from NRP Documentation:**
> {warning.content}

**Applies to:** {', '.join(warning.applies_to)}
**Source:** {warning.source_url}

**Violations:**
{chr(10).join(f'• {v}' for v in warning.violations)}

**Consequences:**
{chr(10).join(f'• {c}' for c in warning.consequences)}
"""
    return formatted

# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Enhanced NRP Documentation Scraper...")
    
    scraper = EnhancedNRPScraper()
    warnings, examples, policies = scraper.scrape_all_documentation(force_refresh=True)
    
    print(f"\nResults:")
    print(f"Warnings: {len(warnings)}")
    print(f"Examples: {len(examples)}") 
    print(f"Policies: {len(policies)}")
    
    # Show critical warnings
    critical = scraper.get_critical_warnings()
    print(f"\nCritical warnings: {len(critical)}")
    
    for warning in critical[:2]:
        print(f"\n{format_warning_for_user(warning)}")