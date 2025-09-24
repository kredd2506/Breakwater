#!/usr/bin/env python3
"""
Template Generator from Scraped YAML Examples
============================================
Generates comprehensive templates from 261 extracted YAML examples
with proper A100 GPU configurations based on authentic NRP documentation.
"""

import json
import re
from pathlib import Path
import yaml

class TemplateGenerator:
    """Generate comprehensive templates from scraped YAML examples"""

    def __init__(self):
        self.load_scraped_data()
        self.load_a100_fixes()
        self.templates = {}

    def load_scraped_data(self):
        """Load the comprehensive scraped data"""
        try:
            scrape_path = Path("D:/Gsoc Gitlab/ocean/breakwater/mcp/cache/enhanced_comprehensive_scrape.json")
            with open(scrape_path, 'r', encoding='utf-8') as f:
                self.scraped_data = json.load(f)
            print(f"[LOADED] Scraped data from {len(self.scraped_data['pages'])} pages")
        except Exception as e:
            print(f"[ERROR] Could not load scraped data: {e}")
            self.scraped_data = None

    def load_a100_fixes(self):
        """Load the A100 template fixes"""
        try:
            a100_path = Path("D:/Gsoc Gitlab/ocean/breakwater/mcp/cache/a100_template_fixes.json")
            with open(a100_path, 'r', encoding='utf-8') as f:
                self.a100_fixes = json.load(f)
            print(f"[LOADED] {len(self.a100_fixes)} A100 template fixes")
        except Exception as e:
            print(f"[ERROR] Could not load A100 fixes: {e}")
            self.a100_fixes = {}

    def classify_yaml_content(self, yaml_content):
        """Classify YAML content by type and purpose"""
        content_lower = yaml_content.lower()

        # Resource type detection
        if 'kind: pod' in content_lower:
            resource_type = 'Pod'
        elif 'kind: deployment' in content_lower:
            resource_type = 'Deployment'
        elif 'kind: service' in content_lower:
            resource_type = 'Service'
        elif 'kind: job' in content_lower:
            resource_type = 'Job'
        elif 'kind: persistentvolumeclaim' in content_lower:
            resource_type = 'PVC'
        elif 'kind: configmap' in content_lower:
            resource_type = 'ConfigMap'
        elif 'kind: secret' in content_lower:
            resource_type = 'Secret'
        elif 'kind: ingress' in content_lower:
            resource_type = 'Ingress'
        else:
            resource_type = 'Other'

        # Feature detection
        features = []
        if 'nvidia.com/gpu' in content_lower or 'nvidia.com/a100' in content_lower:
            features.append('GPU')
        if 'a100' in content_lower:
            features.append('A100')
        if 'persistent' in content_lower or 'pvc' in content_lower:
            features.append('Storage')
        if 'jupyter' in content_lower:
            features.append('Jupyter')
        if 'tensorflow' in content_lower or 'pytorch' in content_lower:
            features.append('ML')
        if 'ingress' in content_lower or 'service' in content_lower:
            features.append('Networking')

        return resource_type, features

    def create_a100_gpu_template(self):
        """Create proper A100 GPU template from authentic examples"""
        # Get the authentic A100 example from NRP docs
        authentic_a100 = None
        for config_name, config_data in self.a100_fixes.items():
            if 'nvidia.com/a100: 1' in config_data['original_yaml']:
                authentic_a100 = config_data['original_yaml']
                break

        if not authentic_a100:
            print("[WARNING] No authentic A100 config found")
            return

        # Clean and format the authentic A100 template
        cleaned_yaml = self.clean_yaml_for_template(authentic_a100)

        # Create parameterized template
        template = {
            'name': 'A100_GPU_Pod',
            'description': 'Authentic A100 GPU Pod template from NRP documentation',
            'resource_type': 'Pod',
            'features': ['GPU', 'A100'],
            'source': 'NRP Official Documentation - GPU Pods',
            'template_yaml': cleaned_yaml,
            'variables': {
                'APP_NAME': 'gpu-app',
                'NAMESPACE': 'gsoc',
                'IMAGE': 'tensorflow/tensorflow:latest-gpu',
                'A100_COUNT': '1',
                'MEMORY': '8Gi',
                'CPU': '4'
            },
            'usage_notes': [
                'Uses authentic nvidia.com/a100: 1 resource specification',
                'Based on official NRP GPU documentation',
                'Suitable for A100-specific ML workloads',
                'Includes proper resource limits and requests'
            ]
        }

        self.templates['a100_gpu_pod'] = template
        print("[TEMPLATE] Created authentic A100 GPU Pod template")

    def clean_yaml_for_template(self, raw_yaml):
        """Clean and format YAML for template use"""
        # Add proper spacing and newlines
        lines = []
        for line in raw_yaml.split('\n'):
            if line.strip():
                lines.append(line)

        # Basic formatting fixes
        formatted = '\n'.join(lines)

        # Fix common formatting issues
        formatted = re.sub(r'(kind:\s*\w+)', r'\1\n', formatted)
        formatted = re.sub(r'(metadata:)', r'\n\1', formatted)
        formatted = re.sub(r'(spec:)', r'\n\1', formatted)

        return formatted

    def generate_comprehensive_templates(self):
        """Generate comprehensive templates from all scraped YAML"""
        template_count = 0

        for page_name, page_data in self.scraped_data['pages'].items():
            if not page_data.get('yaml_examples'):
                continue

            for i, yaml_example in enumerate(page_data['yaml_examples']):
                yaml_content = yaml_example['content']
                resource_type, features = self.classify_yaml_content(yaml_content)

                # Create template
                template_name = f"{page_name}_{resource_type.lower()}_{i+1}"
                template = {
                    'name': template_name,
                    'description': f"{resource_type} template from {page_name}",
                    'resource_type': resource_type,
                    'features': features,
                    'source': yaml_example['source_url'],
                    'template_yaml': yaml_content,
                    'page_context': page_name
                }

                # Special handling for GPU templates
                if 'GPU' in features:
                    if 'A100' in features:
                        # Ensure proper A100 resource specification
                        template['template_yaml'] = re.sub(
                            r'nvidia\.com/gpu:',
                            'nvidia.com/a100:',
                            template['template_yaml']
                        )
                        template['gpu_type'] = 'A100'
                    else:
                        template['gpu_type'] = 'Generic'

                self.templates[template_name] = template
                template_count += 1

        print(f"[GENERATED] {template_count} templates from scraped YAML examples")

    def save_template_database(self):
        """Save comprehensive template database"""
        template_db = {
            'metadata': {
                'total_templates': len(self.templates),
                'source_pages': len(self.scraped_data['pages']) if self.scraped_data else 0,
                'authentic_a100_templates': len([t for t in self.templates.values() if 'A100' in t.get('features', [])]),
                'resource_types': list(set(t['resource_type'] for t in self.templates.values())),
                'generation_timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            },
            'templates': self.templates
        }

        # Save template database
        template_path = Path("D:/Gsoc Gitlab/ocean/breakwater/mcp/cache/comprehensive_template_database.json")
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template_db, f, indent=2, ensure_ascii=False)

        print(f"[SAVED] Comprehensive template database: {template_path}")
        return template_db

    def generate_python_template_module(self, template_db):
        """Generate Python module for easy template access"""
        python_code = '''#!/usr/bin/env python3
"""
NRP Comprehensive Template Database
==================================
Auto-generated comprehensive template database from all 261 YAML examples
scraped from NRP documentation with authentic A100 GPU configurations.
"""

import re

# Comprehensive NRP Template Database
NRP_TEMPLATES = {
'''

        # Add all templates
        for template_name, template_data in template_db['templates'].items():
            python_code += f'    "{template_name}": {{\n'
            python_code += f'        "name": "{template_data["name"]}",\n'
            python_code += f'        "description": "{template_data["description"]}",\n'
            python_code += f'        "resource_type": "{template_data["resource_type"]}",\n'
            python_code += f'        "features": {template_data["features"]},\n'
            python_code += f'        "source": "{template_data["source"]}",\n'

            # Escape the YAML content for Python string
            yaml_escaped = template_data["template_yaml"].replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            python_code += f'        "template_yaml": """{yaml_escaped}""",\n'

            if 'gpu_type' in template_data:
                python_code += f'        "gpu_type": "{template_data["gpu_type"]}",\n'

            python_code += '    },\n'

        python_code += '}\n\n'

        # Add utility functions
        python_code += '''
def get_a100_templates():
    """Get all authentic A100 GPU templates"""
    return {name: template for name, template in NRP_TEMPLATES.items()
            if 'A100' in template.get('features', [])}

def get_templates_by_type(resource_type):
    """Get templates by Kubernetes resource type"""
    return {name: template for name, template in NRP_TEMPLATES.items()
            if template['resource_type'].lower() == resource_type.lower()}

def search_templates(query):
    """Search templates by keyword"""
    query_lower = query.lower()
    matches = []

    for name, template in NRP_TEMPLATES.items():
        score = 0

        # Check name and description
        if query_lower in template['name'].lower():
            score += 3
        if query_lower in template['description'].lower():
            score += 2

        # Check features
        for feature in template['features']:
            if query_lower in feature.lower():
                score += 2

        # Check YAML content
        if query_lower in template['template_yaml'].lower():
            score += 1

        if score > 0:
            matches.append({
                'name': name,
                'template': template,
                'score': score
            })

    # Sort by relevance
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches[:10]

def get_a100_pod_template():
    """Get the authentic A100 GPU Pod template"""
    a100_templates = get_a100_templates()
    for name, template in a100_templates.items():
        if template['resource_type'] == 'Pod':
            return template
    return None

# Template Statistics
TEMPLATE_STATS = {
    'total_templates': len(NRP_TEMPLATES),
    'a100_templates': len(get_a100_templates()),
    'resource_types': list(set(t['resource_type'] for t in NRP_TEMPLATES.values())),
    'features': list(set(f for t in NRP_TEMPLATES.values() for f in t.get('features', [])))
}

print(f"NRP Comprehensive Template Database loaded: {TEMPLATE_STATS['total_templates']} templates")
print(f"A100 GPU templates available: {TEMPLATE_STATS['a100_templates']}")
'''

        # Save Python module
        python_path = Path("D:/Gsoc Gitlab/ocean/breakwater/mcp/cache/nrp_comprehensive_templates.py")
        with open(python_path, 'w', encoding='utf-8') as f:
            f.write(python_code)

        print(f"[PYTHON] Comprehensive template module generated: {python_path}")

def main():
    """Generate comprehensive templates from scraped documentation"""
    generator = TemplateGenerator()

    # Create authentic A100 template
    generator.create_a100_gpu_template()

    # Generate comprehensive templates from all YAML examples
    generator.generate_comprehensive_templates()

    # Save template database
    template_db = generator.save_template_database()

    # Generate Python module
    generator.generate_python_template_module(template_db)

    print(f"\n[TEMPLATE GENERATION COMPLETE]")
    print(f"Total templates generated: {len(generator.templates)}")
    print(f"A100 templates: {len([t for t in generator.templates.values() if 'A100' in t.get('features', [])])}")
    print(f"Resource types: {set(t['resource_type'] for t in generator.templates.values())}")

if __name__ == "__main__":
    import time
    main()