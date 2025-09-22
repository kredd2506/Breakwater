#!/usr/bin/env python3
"""
Enhanced Content Extractor for NRP Documentation
================================================
Extracts and properly formats:
- Caution and note sections
- Special examples (A100 GPU requests, etc.)
- Code blocks and YAML configurations
- Highlighted instructions and warnings
"""

import re
import json
import sqlite3
from typing import Dict, List, Any, Optional
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString

class EnhancedNRPContentExtractor:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def extract_special_sections(self, content: str, url: str) -> Dict[str, Any]:
        """Extract cautions, notes, examples, and special sections"""
        soup = BeautifulSoup(content, 'html.parser')

        extracted = {
            'cautions': [],
            'notes': [],
            'warnings': [],
            'examples': [],
            'code_blocks': [],
            'yaml_configs': [],
            'special_instructions': [],
            'gpu_examples': [],
            'a100_examples': []
        }

        # Extract caution sections
        cautions = soup.find_all(['div', 'p', 'section'], class_=re.compile(r'caution|alert|warning', re.I))
        for caution in cautions:
            text = caution.get_text().strip()
            if text and len(text) > 10:
                extracted['cautions'].append({
                    'text': text,
                    'html': str(caution),
                    'type': 'caution'
                })

        # Extract note sections
        notes = soup.find_all(['div', 'p', 'section'], class_=re.compile(r'note|info|tip', re.I))
        for note in notes:
            text = note.get_text().strip()
            if text and len(text) > 10:
                extracted['notes'].append({
                    'text': text,
                    'html': str(note),
                    'type': 'note'
                })

        # Extract code blocks
        code_blocks = soup.find_all(['pre', 'code'])
        for code in code_blocks:
            code_text = code.get_text().strip()
            if code_text and len(code_text) > 20:
                extracted['code_blocks'].append({
                    'code': code_text,
                    'language': code.get('class', [''])[0] if code.get('class') else 'text',
                    'type': 'code_block'
                })

        # Extract YAML configurations
        yaml_patterns = [
            r'```ya?ml\s*([\s\S]*?)```',
            r'<pre[^>]*class="[^"]*ya?ml[^"]*"[^>]*>([\s\S]*?)</pre>',
            r'(apiVersion:\s*[\w/]+[\s\S]*?)(?=\n\s*(?:apiVersion|---|$))'
        ]

        for pattern in yaml_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                yaml_content = match.strip()
                if yaml_content and len(yaml_content) > 10:
                    extracted['yaml_configs'].append({
                        'yaml': yaml_content,
                        'type': 'yaml_config'
                    })

        # Extract GPU-specific examples
        gpu_patterns = [
            r'(nvidia\.com/gpu:\s*\d+)',
            r'(requests:\s*\n\s*nvidia\.com/gpu:\s*\d+)',
            r'(limits:\s*\n\s*nvidia\.com/gpu:\s*\d+)',
            r'(gpu:\s*\d+)',
            r'(A100[\s\S]*?example[\s\S]*?yaml)',
            r'(To request.*?A100[\s\S]*?:)',
        ]

        text_content = soup.get_text()
        for pattern in gpu_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if 'gpu' in match.lower() or 'a100' in match.lower():
                    extracted['gpu_examples'].append({
                        'text': match.strip(),
                        'type': 'gpu_example'
                    })

        # Extract A100-specific content
        a100_patterns = [
            r'(A100[\s\S]{0,200}?request[\s\S]{0,200}?yaml)',
            r'(To request.*?A100[\s\S]{0,500}?:)',
            r'(For A100[\s\S]{0,300}?example)',
            r'(nvidia\.com/gpu:\s*1[\s\S]{0,100}?A100)',
        ]

        for pattern in a100_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                extracted['a100_examples'].append({
                    'text': match.strip(),
                    'type': 'a100_specific'
                })

        # Extract special instructions (numbered lists, highlighted sections)
        instructions = soup.find_all(['ol', 'ul', 'div'], class_=re.compile(r'instruction|step|highlight', re.I))
        for instruction in instructions:
            text = instruction.get_text().strip()
            if text and len(text) > 20:
                extracted['special_instructions'].append({
                    'text': text,
                    'html': str(instruction),
                    'type': 'instruction'
                })

        # Look for highlighted warning text
        warning_keywords = ['caution', 'warning', 'important', 'note', 'attention']
        paragraphs = soup.find_all(['p', 'div', 'span'])
        for p in paragraphs:
            text = p.get_text().lower().strip()
            if any(keyword in text for keyword in warning_keywords) and len(text) > 15:
                extracted['warnings'].append({
                    'text': p.get_text().strip(),
                    'html': str(p),
                    'type': 'warning'
                })

        return extracted

    def get_enhanced_page_content(self, path: str) -> Optional[Dict[str, Any]]:
        """Get enhanced page content with special sections extracted"""
        if not self.db_path.exists():
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("""
                SELECT url, title, content, content_length, yaml_blocks, keywords, crawled_at
                FROM crawled_pages WHERE path = ? OR url LIKE ?
                ORDER BY content_length DESC LIMIT 1
            """, (path, f"%{path}%"))

            row = cursor.fetchone()
            conn.close()

            if row:
                url, title, full_content, content_length, yaml_blocks, keywords, crawled_at = row

                # Extract special sections
                special_sections = self.extract_special_sections(full_content, url)

                return {
                    'url': url,
                    'title': title,
                    'content_length': content_length,
                    'keywords': json.loads(keywords or '[]'),
                    'crawled_at': crawled_at,
                    'special_sections': special_sections,
                    'content_preview': full_content[:2000],
                    'status': 'enhanced_extraction_complete'
                }

            return None

        except Exception as e:
            return {'error': str(e)}

def test_gpu_page_extraction():
    """Test extraction on GPU pods page"""
    db_path = Path(__file__).parent / "nrp_crawled_data" / "nrp_crawled_docs.db"
    extractor = EnhancedNRPContentExtractor(db_path)

    # Test GPU pods page
    gpu_page = extractor.get_enhanced_page_content('/documentation/userdocs/running/gpu-pods')

    if gpu_page and 'special_sections' in gpu_page:
        sections = gpu_page['special_sections']

        print("GPU Pods Page - Enhanced Content Extraction")
        print("=" * 60)
        print(f"Title: {gpu_page['title']}")
        print(f"Content Length: {gpu_page['content_length']} chars")
        print()

        # Show cautions
        if sections['cautions']:
            print(f"CAUTIONS ({len(sections['cautions'])}):")
            for i, caution in enumerate(sections['cautions'][:3], 1):
                print(f"  {i}. {caution['text'][:200]}...")
            print()

        # Show notes
        if sections['notes']:
            print(f"NOTES ({len(sections['notes'])}):")
            for i, note in enumerate(sections['notes'][:3], 1):
                print(f"  {i}. {note['text'][:200]}...")
            print()

        # Show GPU examples
        if sections['gpu_examples']:
            print(f"GPU EXAMPLES ({len(sections['gpu_examples'])}):")
            for i, example in enumerate(sections['gpu_examples'][:5], 1):
                print(f"  {i}. {example['text'][:150]}...")
            print()

        # Show A100 specific examples
        if sections['a100_examples']:
            print(f"A100 EXAMPLES ({len(sections['a100_examples'])}):")
            for i, example in enumerate(sections['a100_examples'], 1):
                print(f"  {i}. {example['text'][:200]}...")
            print()

        # Show YAML configs
        if sections['yaml_configs']:
            print(f"YAML CONFIGURATIONS ({len(sections['yaml_configs'])}):")
            for i, yaml_config in enumerate(sections['yaml_configs'][:3], 1):
                print(f"  {i}. {yaml_config['yaml'][:100]}...")
            print()

        # Show code blocks
        if sections['code_blocks']:
            print(f"CODE BLOCKS ({len(sections['code_blocks'])}):")
            for i, code in enumerate(sections['code_blocks'][:3], 1):
                print(f"  {i}. ({code['language']}) {code['code'][:100]}...")
            print()

    else:
        print("GPU page not found or extraction failed")

if __name__ == "__main__":
    test_gpu_page_extraction()