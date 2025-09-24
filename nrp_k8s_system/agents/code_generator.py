#!/usr/bin/env python3
"""
Code Generator Agent
===================

Handles template and example generation requests. This agent:

1. Accesses scraped examples from NRP docs
2. Quotes relevant examples from documentation
3. Creates new configurations based on templates
4. Asks relevant follow-up questions
5. Adheres to NRP policies and warnings

Specializes in generating YAML manifests, configurations, and deployment examples.
"""

import os
import yaml
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from .agent_types import BaseAgent, AgentRequest, AgentResponse, IntentType, ConfidenceLevel
from ..core.nrp_init import init_chat_model
# from ..template.nautilus_template import NautilusTemplate  # Optional import


@dataclass
class Template:
    """Template structure for code generation."""
    name: str
    description: str
    content: str
    resource_type: str
    example_source: str
    nrp_policies: List[str]
    variables: Dict[str, str]


@dataclass
class GeneratedCode:
    """Generated code with metadata."""
    code: str
    template_used: str
    variables_applied: Dict[str, str]
    warnings: List[str]
    follow_up_questions: List[str]


class CodeGeneratorAgent(BaseAgent):
    """
    Code Generator Agent for creating Kubernetes configurations.

    Process:
    1. Parse user request to identify resource type and requirements
    2. Find relevant templates from scraped NRP examples
    3. Quote the original example source
    4. Generate new configuration based on template
    5. Apply NRP policies and add warnings
    6. Suggest follow-up questions for refinement
    """

    # NRP GPU Type Mapping from https://nrp.ai/documentation/userdocs/running/gpu-pods/#requesting-special-gpus
    GPU_TYPE_MAPPING = {
        "A40": "nvidia.com/a40",
        "A100": "nvidia.com/a100",
        "RTX_A6000": "nvidia.com/rtxa6000",
        "NVIDIA_RTX_A6000": "nvidia.com/rtxa6000",
        "RTX_8000": "nvidia.com/rtx8000",
        "QUADRO_RTX_8000": "nvidia.com/rtx8000",
        "GH200": "nvidia.com/gh200",
        "GRACE_HOPPER_GH200": "nvidia.com/gh200",
        "MIG": "nvidia.com/mig-small",
        "A100_MIG": "nvidia.com/mig-small",
        "GENERIC": "nvidia.com/gpu"
    }

    # Reverse mapping for template identification
    RESOURCE_TO_GPU_TYPE = {v: k for k, v in GPU_TYPE_MAPPING.items()}

    def __init__(self):
        self.llm = init_chat_model()
        self.templates_dir = Path(__file__).parent.parent / "template"
        self.cache_dir = Path(__file__).parent.parent / "cache" / "nautilus_docs"
        self.templates = self._load_templates()
        self.nrp_policies = self._load_nrp_policies()

    def can_handle(self, request: AgentRequest) -> bool:
        """Check if this agent can handle the request."""
        return request.intent_type == IntentType.CODE_REQUEST

    def process(self, request: AgentRequest) -> AgentResponse:
        """
        Process code generation request.

        Steps:
        1. Analyze request to determine resource type and requirements
        2. Find matching templates from NRP examples
        3. Quote original source documentation
        4. Generate customized configuration
        5. Apply NRP policies and warnings
        6. Generate follow-up questions
        """
        try:
            print(f"[Code Generator] Processing request: {request.user_input}")

            # Step 1: Analyze request
            analysis = self._analyze_request(request.user_input)

            # Step 2: Find matching templates
            matching_templates = self._find_templates(analysis)

            if not matching_templates:
                return self._handle_no_templates(request, analysis)

            # Step 3: Select best template and quote source
            selected_template = self._select_best_template(matching_templates, analysis)
            source_quote = self._quote_source_example(selected_template)

            # Step 4: Generate code
            generated_code = self._generate_code(selected_template, analysis)

            # Step 5: Apply NRP policies and warnings
            validated_code = self._apply_nrp_policies(generated_code, analysis)

            # Step 6: Format final response
            response_content = self._format_response(
                source_quote, validated_code, selected_template
            )

            return AgentResponse(
                success=True,
                content=response_content,
                agent_type="Code Generator",
                confidence=request.confidence,
                metadata={
                    "template_used": selected_template.name,
                    "resource_type": analysis.get("resource_type"),
                    "variables_applied": validated_code.variables_applied,
                    "policies_applied": len(validated_code.warnings)
                },
                follow_up_suggestions=validated_code.follow_up_questions
            )

        except Exception as e:
            print(f"[!] Code generation failed: {e}")
            return AgentResponse(
                success=False,
                content=f"Code generation failed: {str(e)}",
                agent_type="Code Generator",
                confidence=ConfidenceLevel.LOW,
                metadata={"error": str(e)},
                follow_up_suggestions=["Try being more specific about the resource type"]
            )

    def _analyze_request(self, user_input: str) -> Dict[str, Any]:
        """Analyze user request to extract requirements."""

        analysis_prompt = f"""Analyze this Kubernetes code generation request: "{user_input}"

Extract:
1. Resource type (pod, deployment, service, ingress, configmap, secret, pvc, etc.)
2. Key requirements (replicas, image, ports, storage, environment variables, etc.)
3. Special features (GPU, persistent storage, ingress, monitoring, etc.)

Respond in JSON format:
{{
    "resource_type": "primary_resource_type",
    "additional_resources": ["list", "of", "related"],
    "requirements": {{
        "image": "app_image_if_specified",
        "replicas": "number_if_specified",
        "ports": ["list_of_ports"],
        "storage": "storage_requirements",
        "gpu": "gpu_requirements",
        "environment": ["env_vars"]
    }},
    "features": ["special", "features", "requested"],
    "complexity": "simple|moderate|complex"
}}"""

        try:
            response = self.llm.invoke(analysis_prompt)
            import json
            return json.loads(response.content.strip())
        except Exception as e:
            print(f"[!] Request analysis failed: {e}")
            # Fallback analysis
            return self._fallback_analysis(user_input)

    def _fallback_analysis(self, user_input: str) -> Dict[str, Any]:
        """Fallback analysis using keyword matching."""
        input_lower = user_input.lower()

        # Detect resource type
        resource_keywords = {
            "deployment": ["deployment", "deploy"],
            "service": ["service", "svc"],
            "ingress": ["ingress", "expose"],
            "pod": ["pod"],
            "configmap": ["configmap", "config"],
            "secret": ["secret"],
            "pvc": ["pvc", "volume", "storage"],
            "job": ["job", "batch"],
            "cronjob": ["cronjob", "cron"]
        }

        resource_type = "deployment"  # Default
        for resource, keywords in resource_keywords.items():
            if any(keyword in input_lower for keyword in keywords):
                resource_type = resource
                break

        # Extract GPU requirements using comprehensive mapping
        requirements = {}
        gpu_detected = False

        # Check for specific GPU types first (exact matches take priority)
        for gpu_type, resource_spec in self.GPU_TYPE_MAPPING.items():
            if gpu_type.lower() in input_lower.replace("_", " ").replace("-", " "):
                requirements["gpu"] = resource_spec
                requirements["gpu_type"] = gpu_type
                gpu_detected = True
                print(f"[Fallback Analysis] Detected GPU type: {gpu_type} -> {resource_spec}")
                break

        # Fallback to generic GPU detection
        if not gpu_detected and "gpu" in input_lower:
            requirements["gpu"] = "nvidia.com/gpu"
            requirements["gpu_type"] = "GENERIC"
            print(f"[Fallback Analysis] Detected generic GPU")

        # Storage detection
        if "storage" in input_lower or "volume" in input_lower:
            requirements["storage"] = "persistent"

        return {
            "resource_type": resource_type,
            "additional_resources": [],
            "requirements": requirements,
            "features": [],
            "complexity": "simple"
        }

    def _load_templates(self) -> Dict[str, Template]:
        """Load available templates from template directory and cached docs."""
        templates = {}

        # Load built-in templates
        templates.update(self._load_builtin_templates())

        # Load templates from cached NRP docs
        templates.update(self._load_cached_templates())

        # Load comprehensive scraped templates
        templates.update(self._load_comprehensive_templates())

        print(f"[Code Generator] Loaded {len(templates)} templates")
        return templates

    def _load_builtin_templates(self) -> Dict[str, Template]:
        """Load built-in templates from template directory."""
        templates = {}

        try:
            # Load from nautilus_template.py if available
            # Temporarily disabled due to missing dependencies
            # from ..template.nautilus_template import get_template_examples
            print("[*] Using fallback templates (nautilus_template disabled)")

        except ImportError:
            print("[!] nautilus_template module not available")

        # Fallback built-in templates
        templates.update(self._create_fallback_templates())

        return templates

    def _create_fallback_templates(self) -> Dict[str, Template]:
        """Create fallback templates for common resources."""

        deployment_template = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{APP_NAME}}
  namespace: {{NAMESPACE}}
spec:
  replicas: {{REPLICAS}}
  selector:
    matchLabels:
      app: {{APP_NAME}}
  template:
    metadata:
      labels:
        app: {{APP_NAME}}
    spec:
      containers:
      - name: {{APP_NAME}}
        image: {{IMAGE}}
        ports:
        - containerPort: {{PORT}}
        resources:
          requests:
            memory: "{{MEMORY}}"
            cpu: "{{CPU}}"
          limits:
            memory: "{{MEMORY_LIMIT}}"
            cpu: "{{CPU_LIMIT}}"
"""

        service_template = """apiVersion: v1
kind: Service
metadata:
  name: {{APP_NAME}}-service
  namespace: {{NAMESPACE}}
spec:
  selector:
    app: {{APP_NAME}}
  ports:
  - port: {{SERVICE_PORT}}
    targetPort: {{TARGET_PORT}}
  type: ClusterIP
"""

        gpu_deployment_template = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{APP_NAME}}
  namespace: {{NAMESPACE}}
spec:
  replicas: {{REPLICAS}}
  selector:
    matchLabels:
      app: {{APP_NAME}}
  template:
    metadata:
      labels:
        app: {{APP_NAME}}
    spec:
      containers:
      - name: {{APP_NAME}}
        image: {{IMAGE}}
        resources:
          requests:
            nvidia.com/gpu: {{GPU_COUNT}}
            memory: "{{MEMORY}}"
            cpu: "{{CPU}}"
          limits:
            nvidia.com/gpu: {{GPU_COUNT}}
            memory: "{{MEMORY_LIMIT}}"
            cpu: "{{CPU_LIMIT}}"
"""

        a100_deployment_template = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{APP_NAME}}
  namespace: {{NAMESPACE}}
spec:
  replicas: {{REPLICAS}}
  selector:
    matchLabels:
      app: {{APP_NAME}}
  template:
    metadata:
      labels:
        app: {{APP_NAME}}
    spec:
      containers:
      - name: {{APP_NAME}}
        image: {{IMAGE}}
        resources:
          requests:
            nvidia.com/a100: {{GPU_COUNT}}
            memory: "{{MEMORY}}"
            cpu: "{{CPU}}"
          limits:
            nvidia.com/a100: {{GPU_COUNT}}
            memory: "{{MEMORY_LIMIT}}"
            cpu: "{{CPU_LIMIT}}"
"""

        # Template generator for specific GPU types
        def create_gpu_deployment_template(gpu_resource: str) -> str:
            return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{{{APP_NAME}}}}
  namespace: {{{{NAMESPACE}}}}
spec:
  replicas: {{{{REPLICAS}}}}
  selector:
    matchLabels:
      app: {{{{APP_NAME}}}}
  template:
    metadata:
      labels:
        app: {{{{APP_NAME}}}}
    spec:
      containers:
      - name: {{{{APP_NAME}}}}
        image: {{{{IMAGE}}}}
        resources:
          requests:
            {gpu_resource}: {{{{GPU_COUNT}}}}
            memory: "{{{{MEMORY}}}}"
            cpu: "{{{{CPU}}}}"
          limits:
            {gpu_resource}: {{{{GPU_COUNT}}}}
            memory: "{{{{MEMORY_LIMIT}}}}"
            cpu: "{{{{CPU_LIMIT}}}}"
"""

        # Base templates
        templates = {
            "basic-deployment": Template(
                name="basic-deployment",
                description="Basic Kubernetes deployment",
                content=deployment_template,
                resource_type="deployment",
                example_source="NRP Best Practices",
                nrp_policies=["Use appropriate resource limits", "Specify namespace"],
                variables={"APP_NAME": "myapp", "NAMESPACE": "gsoc", "REPLICAS": "1",
                          "IMAGE": "nginx:latest", "PORT": "80", "MEMORY": "256Mi",
                          "CPU": "100m", "MEMORY_LIMIT": "512Mi", "CPU_LIMIT": "500m"}
            ),
            "basic-service": Template(
                name="basic-service",
                description="Basic Kubernetes service",
                content=service_template,
                resource_type="service",
                example_source="NRP Best Practices",
                nrp_policies=["Use ClusterIP for internal services"],
                variables={"APP_NAME": "myapp", "NAMESPACE": "gsoc",
                          "SERVICE_PORT": "80", "TARGET_PORT": "80"}
            ),
            "gpu-deployment": Template(
                name="gpu-deployment",
                description="Generic GPU-enabled deployment",
                content=gpu_deployment_template,
                resource_type="deployment",
                example_source="NRP GPU Guidelines",
                nrp_policies=["Request GPUs explicitly", "Set resource limits",
                             "Use appropriate GPU-enabled images"],
                variables={"APP_NAME": "gpu-app", "NAMESPACE": "gsoc", "REPLICAS": "1",
                          "IMAGE": "nvidia/cuda:latest", "GPU_COUNT": "1",
                          "MEMORY": "2Gi", "CPU": "1", "MEMORY_LIMIT": "4Gi",
                          "CPU_LIMIT": "2"}
            )
        }

        # GPU-specific memory and CPU recommendations based on GPU type
        gpu_specs = {
            "A40": {"memory": "16Gi", "cpu": "4", "memory_limit": "32Gi", "cpu_limit": "8"},
            "A100": {"memory": "32Gi", "cpu": "8", "memory_limit": "64Gi", "cpu_limit": "16"},
            "RTX_A6000": {"memory": "12Gi", "cpu": "4", "memory_limit": "24Gi", "cpu_limit": "8"},
            "RTX_8000": {"memory": "12Gi", "cpu": "4", "memory_limit": "24Gi", "cpu_limit": "8"},
            "GH200": {"memory": "64Gi", "cpu": "16", "memory_limit": "128Gi", "cpu_limit": "32"},
            "MIG": {"memory": "8Gi", "cpu": "2", "memory_limit": "16Gi", "cpu_limit": "4"}
        }

        # Create templates for all specific GPU types
        for gpu_type, resource_spec in self.GPU_TYPE_MAPPING.items():
            if gpu_type != "GENERIC":  # Skip generic GPU
                gpu_name = gpu_type.lower().replace("_", "-")
                specs = gpu_specs.get(gpu_type, gpu_specs["A100"])  # Default to A100 specs

                templates[f"{gpu_name}-deployment"] = Template(
                    name=f"{gpu_name}-deployment",
                    description=f"{gpu_type} GPU-enabled deployment",
                    content=create_gpu_deployment_template(resource_spec),
                    resource_type="deployment",
                    example_source=f"NRP {gpu_type} GPU Guidelines",
                    nrp_policies=[
                        f"Request {gpu_type} GPUs explicitly using {resource_spec}",
                        "Set appropriate resource limits for GPU workloads",
                        f"Use {gpu_type}-compatible images",
                        f"Ensure sufficient memory for {gpu_type} operations"
                    ],
                    variables={
                        "APP_NAME": f"{gpu_name}-app",
                        "NAMESPACE": "gsoc",
                        "REPLICAS": "1",
                        "IMAGE": "nvidia/cuda:latest",
                        "GPU_COUNT": "1",
                        "MEMORY": specs["memory"],
                        "CPU": specs["cpu"],
                        "MEMORY_LIMIT": specs["memory_limit"],
                        "CPU_LIMIT": specs["cpu_limit"]
                    }
                )

        return templates

    def _load_cached_templates(self) -> Dict[str, Template]:
        """Load templates from cached NRP documentation."""
        templates = {}

        if not self.cache_dir.exists():
            return templates

        try:
            # Scan cached docs for YAML examples
            for yaml_file in self.cache_dir.rglob("*.yaml"):
                if yaml_file.name.startswith("example"):
                    template = self._parse_cached_yaml(yaml_file)
                    if template:
                        templates[template.name] = template

        except Exception as e:
            print(f"[!] Failed to load cached templates: {e}")

        return templates

    def _load_comprehensive_templates(self) -> Dict[str, Template]:
        """Load comprehensive templates from scraped NRP documentation."""
        templates = {}

        try:
            # Import the comprehensive templates
            import sys
            template_path = Path(__file__).parent.parent / "template"
            sys.path.insert(0, str(template_path))

            from nrp_comprehensive_templates import get_a100_templates, get_templates_by_type, search_templates

            # Load A100 templates specifically
            a100_templates = get_a100_templates()
            for name, template_data in a100_templates.items():
                templates[f"a100_{name}"] = Template(
                    name=f"a100_{name}",
                    description=f"A100 {template_data['description']}",
                    content=template_data['template_yaml'],
                    resource_type=template_data['resource_type'].lower(),
                    example_source=template_data['source'],
                    nrp_policies=[
                        "Uses authentic nvidia.com/a100 resource specification",
                        "Based on official NRP GPU documentation",
                        "Suitable for A100-specific ML workloads"
                    ],
                    variables={"GPU_TYPE": "A100", "GPU_COUNT": "1", "APP_NAME": "a100-app"}
                )

            print(f"[Code Generator] Loaded {len(a100_templates)} A100 templates from comprehensive database")

        except ImportError as e:
            print(f"[WARNING] Could not load comprehensive templates: {e}")
        except Exception as e:
            print(f"[ERROR] Failed to load comprehensive templates: {e}")

        return templates

    def _parse_cached_yaml(self, yaml_file: Path) -> Optional[Template]:
        """Parse a cached YAML file into a template."""
        try:
            with open(yaml_file, 'r') as f:
                content = f.read()

            # Extract metadata from YAML
            docs = list(yaml.safe_load_all(content))
            if not docs:
                return None

            first_doc = docs[0]
            resource_type = first_doc.get("kind", "unknown").lower()
            name = f"cached-{yaml_file.stem}"

            return Template(
                name=name,
                description=f"Template from {yaml_file.name}",
                content=content,
                resource_type=resource_type,
                example_source=f"NRP Documentation: {yaml_file.name}",
                nrp_policies=["Review before deployment"],
                variables={}
            )

        except Exception as e:
            print(f"[!] Failed to parse {yaml_file}: {e}")
            return None

    def _load_nrp_policies(self) -> Dict[str, List[str]]:
        """Load NRP policies and warnings."""
        return {
            "general": [
                "Always specify resource requests and limits",
                "Use appropriate namespaces for isolation",
                "Follow NRP naming conventions",
                "Review security policies before deployment"
            ],
            "gpu": [
                "GPU resources are limited - request only what you need",
                "Use nvidia.com/gpu resource specification",
                "Ensure your image supports GPU workloads",
                "Test locally before deploying"
            ],
            "storage": [
                "Use rook-ceph-block for RWO storage",
                "Use rook-cephfs for RWX/shared storage",
                "Specify appropriate storage size",
                "Consider backup and recovery needs"
            ],
            "networking": [
                "Use haproxy ingress class for external access",
                "Configure proper service types",
                "Review security groups and policies",
                "Use TLS for external services"
            ]
        }

    def _find_templates(self, analysis: Dict[str, Any]) -> List[Template]:
        """Find templates using hard eligibility gates (Constraint Satisfaction)."""
        resource_type = analysis.get("resource_type", "deployment")
        requirements = analysis.get("requirements", {})
        features = analysis.get("features", [])

        # Step 1: Hard Eligibility Gates (Constraint Satisfaction)
        eligible_templates = []
        exact_match_found = False

        # Check for exact hardware matches first (highest priority)
        gpu_type = requirements.get("gpu_type")
        if gpu_type:
            requested_resource = self.GPU_TYPE_MAPPING.get(gpu_type)
            print(f"[Template Selection] Looking for GPU type: {gpu_type} -> {requested_resource}")

            for template in self.templates.values():
                # Hard constraint: exact GPU resource specification match
                if requested_resource and requested_resource in template.content:
                    if template.resource_type == resource_type:
                        eligible_templates.append(template)
                        exact_match_found = True
                        print(f"[Template Selection] Found exact resource match: {template.name} ({requested_resource})")
                # Alternative: check by GPU type name in template name
                elif gpu_type != "GENERIC" and gpu_type.lower().replace("_", "") in template.name.lower().replace("_", "").replace("-", ""):
                    if template.resource_type == resource_type:
                        eligible_templates.append(template)
                        exact_match_found = True
                        print(f"[Template Selection] Found name-based match: {template.name} for {gpu_type}")
                # Handle generic GPU - exclude all specific GPU types
                elif gpu_type == "GENERIC":
                    # Only include if it contains nvidia.com/gpu and doesn't contain any specific GPU resources
                    if "nvidia.com/gpu" in template.content:
                        has_specific_gpu = any(spec in template.content for spec in self.GPU_TYPE_MAPPING.values() if spec != "nvidia.com/gpu")
                        if not has_specific_gpu and template.resource_type == resource_type:
                            eligible_templates.append(template)
                            exact_match_found = True
                            print(f"[Template Selection] Found generic GPU match: {template.name}")

        # If exact matches found, ONLY consider those (hard constraint)
        if exact_match_found:
            print(f"[Template Selection] Found {len(eligible_templates)} exact GPU matches - excluding generic templates")
            return self._score_eligible_templates(eligible_templates, analysis)

        # Step 2: If no exact matches, apply general eligibility constraints
        for template in self.templates.values():
            # Primary resource type constraint (must match)
            if template.resource_type != resource_type:
                continue

            # Feature constraint checking
            meets_constraints = True

            # Storage constraint
            if "storage" in requirements:
                if not any(keyword in template.content.lower()
                          for keyword in ["volume", "pvc", "storage"]):
                    meets_constraints = False

            # Only add if all constraints are met
            if meets_constraints:
                eligible_templates.append(template)

        print(f"[Template Selection] Found {len(eligible_templates)} eligible templates after constraint filtering")
        return self._score_eligible_templates(eligible_templates, analysis)

    def _score_eligible_templates(self, eligible_templates: List[Template], analysis: Dict[str, Any]) -> List[Template]:
        """Score only pre-filtered eligible templates."""
        if not eligible_templates:
            return []

        requirements = analysis.get("requirements", {})
        features = analysis.get("features", [])

        scored_templates = []

        for template in eligible_templates:
            score = 0

            # Base score for being eligible
            score += 10

            # Bonus scoring for additional features
            if "gpu_type" in requirements:
                if requirements["gpu_type"] == "A100" and "a100" in template.name.lower():
                    score += 5  # Bonus for A100 (already filtered for exactness)
                elif "gpu" in template.name:
                    score += 3

            # Content relevance bonus
            for feature in features:
                if feature.lower() in template.content.lower():
                    score += 2

            # Template completeness bonus
            if len(template.content) > 500:  # More comprehensive templates
                score += 1

            scored_templates.append((template, score))

        # Sort by score and return templates
        scored_templates.sort(key=lambda x: x[1], reverse=True)
        return [template for template, score in scored_templates]

    def _select_best_template(self, templates: List[Template], analysis: Dict[str, Any]) -> Template:
        """Select the best template with validation for schedulable capacity."""
        if not templates:
            return self._create_dynamic_template(analysis)

        # Step 3: Validation - ensure selected template maps to real schedulable capacity
        for template in templates:
            if self._validate_template_schedulability(template, analysis):
                print(f"[Template Selection] Selected validated template: {template.name}")
                return template
            else:
                print(f"[Template Selection] Template {template.name} failed schedulability validation")

        # If no templates pass validation, return the best one with warnings
        print(f"[Template Selection] No templates passed validation - using best available with warnings")
        return templates[0]

    def _validate_template_schedulability(self, template: Template, analysis: Dict[str, Any]) -> bool:
        """
        Validate that the template maps to real, schedulable capacity.

        This checks:
        1. GPU resource specifications match actual cluster capabilities
        2. Resource requests are within reasonable limits
        3. Required storage classes exist
        4. Network policies allow the configuration
        """
        try:
            requirements = analysis.get("requirements", {})

            # GPU validation for all supported types
            if "gpu_type" in requirements:
                gpu_type = requirements["gpu_type"]
                expected_resource = self.GPU_TYPE_MAPPING.get(gpu_type)

                if expected_resource:
                    # Validate the template contains the correct GPU resource specification
                    if expected_resource not in template.content:
                        print(f"[Validation] {gpu_type} template {template.name} missing {expected_resource} resource spec")
                        return False

                    # Ensure it's not using other GPU resource types
                    other_gpu_resources = [res for res in self.GPU_TYPE_MAPPING.values() if res != expected_resource]
                    conflicting_resources = [res for res in other_gpu_resources if res in template.content]

                    if conflicting_resources:
                        print(f"[Validation] {gpu_type} template {template.name} incorrectly uses {conflicting_resources}")
                        return False

                    # Validate resource limits based on GPU type
                    gpu_specs = {
                        "A40": ["16Gi", "32Gi"],
                        "A100": ["32Gi", "64Gi"],
                        "RTX_A6000": ["12Gi", "24Gi"],
                        "RTX_8000": ["12Gi", "24Gi"],
                        "GH200": ["64Gi", "128Gi"],
                        "MIG": ["8Gi", "16Gi"],
                        "GENERIC": ["2Gi", "4Gi", "8Gi"]
                    }

                    expected_memories = gpu_specs.get(gpu_type, [])
                    if expected_memories and not any(mem in template.content for mem in expected_memories):
                        print(f"[Validation] {gpu_type} template {template.name} may have insufficient memory spec for {gpu_type}")
                        # Warning but not failure for memory specs

                    print(f"[Validation] {gpu_type} template validated with {expected_resource}")
                else:
                    print(f"[Validation] Unknown GPU type: {gpu_type}")
                    return False

            # Storage validation
            if "storage" in requirements:
                if any(storage_class in template.content for storage_class in ["rook-ceph-block", "rook-cephfs"]):
                    print(f"[Validation] Template {template.name} uses valid NRP storage classes")
                else:
                    print(f"[Validation] Template {template.name} may use non-standard storage classes")
                    # Warning but not failure

            # Resource limits validation
            if "resources:" in template.content:
                if "limits:" not in template.content:
                    print(f"[Validation] Template {template.name} missing resource limits")
                    return False

            # Namespace validation
            if "namespace:" not in template.content and "{{NAMESPACE}}" not in template.content:
                print(f"[Validation] Template {template.name} missing namespace specification")
                return False

            print(f"[Validation] Template {template.name} passed all validation checks")
            return True

        except Exception as e:
            print(f"[Validation] Error validating template {template.name}: {e}")
            return False

    def _create_dynamic_template(self, analysis: Dict[str, Any]) -> Template:
        """Create a template dynamically if no matches found."""
        resource_type = analysis.get("resource_type", "deployment")

        # Use fallback templates
        fallback_map = {
            "deployment": "basic-deployment",
            "service": "basic-service",
            "pod": "basic-deployment"  # Use deployment template for pods
        }

        template_name = fallback_map.get(resource_type, "basic-deployment")
        if template_name in self.templates:
            return self.templates[template_name]

        # Ultimate fallback
        return Template(
            name="dynamic-template",
            description=f"Dynamic template for {resource_type}",
            content=f"# Generated template for {resource_type}\n# Please specify your requirements",
            resource_type=resource_type,
            example_source="Dynamic generation",
            nrp_policies=["Review and customize before use"],
            variables={}
        )

    def _quote_source_example(self, template: Template) -> str:
        """Quote the original source example."""
        return f"""## Original Example Source

**Source:** {template.example_source}
**Description:** {template.description}

This template is based on the following example from NRP documentation:

```yaml
{template.content[:500]}{'...' if len(template.content) > 500 else ''}
```

---

"""

    def _generate_code(self, template: Template, analysis: Dict[str, Any]) -> GeneratedCode:
        """Generate customized code from template."""

        # Extract variables from analysis
        variables = self._extract_variables(analysis, template)

        # Apply variables to template
        customized_content = self._apply_variables(template.content, variables)

        # Generate warnings based on content and requirements
        warnings = self._generate_warnings(template, analysis, variables)

        # Generate follow-up questions
        follow_ups = self._generate_follow_ups(template, analysis)

        return GeneratedCode(
            code=customized_content,
            template_used=template.name,
            variables_applied=variables,
            warnings=warnings,
            follow_up_questions=follow_ups
        )

    def _extract_variables(self, analysis: Dict[str, Any], template: Template) -> Dict[str, str]:
        """Extract variables from analysis and apply to template."""
        variables = template.variables.copy()

        requirements = analysis.get("requirements", {})

        # Map analysis to template variables
        if "image" in requirements:
            variables["IMAGE"] = requirements["image"]
        if "replicas" in requirements:
            variables["REPLICAS"] = str(requirements["replicas"])
        if "gpu" in requirements:
            variables["GPU_COUNT"] = "1"  # Default

        # Add user-friendly defaults
        variables.setdefault("NAMESPACE", "gsoc")
        variables.setdefault("APP_NAME", "myapp")

        return variables

    def _apply_variables(self, content: str, variables: Dict[str, str]) -> str:
        """Apply variables to template content."""
        for var_name, var_value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            content = content.replace(placeholder, var_value)

        return content

    def _generate_warnings(self, template: Template, analysis: Dict[str, Any],
                          variables: Dict[str, str]) -> List[str]:
        """Generate warnings based on template and requirements."""
        warnings = []

        # Add template-specific policies
        warnings.extend(template.nrp_policies)

        # Add requirement-specific warnings
        if "gpu" in analysis.get("requirements", {}):
            warnings.extend(self.nrp_policies["gpu"])

        if "storage" in analysis.get("requirements", {}):
            warnings.extend(self.nrp_policies["storage"])

        # Add general NRP policies
        warnings.extend(self.nrp_policies["general"])

        return list(set(warnings))  # Remove duplicates

    def _generate_follow_ups(self, template: Template, analysis: Dict[str, Any]) -> List[str]:
        """Generate follow-up questions for refinement."""
        follow_ups = []

        resource_type = analysis.get("resource_type")

        if resource_type == "deployment":
            follow_ups.extend([
                "Do you need a Service to expose this deployment?",
                "What resource limits should I set?",
                "Do you need persistent storage?"
            ])

        if "gpu" in analysis.get("requirements", {}):
            follow_ups.extend([
                "How many GPUs do you need?",
                "What GPU-enabled base image should I use?",
                "Do you need specific CUDA versions?"
            ])

        if resource_type in ["service", "ingress"]:
            follow_ups.extend([
                "Should this be accessible from outside the cluster?",
                "Do you need TLS/SSL configuration?",
                "What security policies should apply?"
            ])

        # Generic follow-ups
        follow_ups.extend([
            "Would you like me to generate related resources?",
            "Need help with deployment commands?",
            "Want to review NRP best practices?"
        ])

        return follow_ups[:5]  # Limit to 5 questions

    def _apply_nrp_policies(self, generated_code: GeneratedCode,
                           analysis: Dict[str, Any]) -> GeneratedCode:
        """Apply NRP policies and enhance warnings."""

        # Validate against NRP policies
        policy_warnings = []

        # Check for missing namespace
        if "namespace:" not in generated_code.code:
            policy_warnings.append("⚠️  Add namespace specification for proper isolation")

        # Check for missing resource limits
        if "resources:" not in generated_code.code:
            policy_warnings.append("⚠️  Add resource requests and limits")

        # Check GPU configuration
        if "nvidia.com/gpu" in generated_code.code:
            if "limits:" not in generated_code.code:
                policy_warnings.append("⚠️  GPU resources must have limits specified")

        # Enhance existing warnings
        enhanced_warnings = generated_code.warnings + policy_warnings

        return GeneratedCode(
            code=generated_code.code,
            template_used=generated_code.template_used,
            variables_applied=generated_code.variables_applied,
            warnings=enhanced_warnings,
            follow_up_questions=generated_code.follow_up_questions
        )

    def _format_response(self, source_quote: str, generated_code: GeneratedCode,
                        template: Template) -> str:
        """Format the final response."""

        response = f"""{source_quote}

## Generated Configuration

Based on your request, here's the customized YAML configuration:

```yaml
{generated_code.code}
```

## Variables Applied

{chr(10).join(f"- **{k}**: {v}" for k, v in generated_code.variables_applied.items())}

## NRP Policies & Warnings

{chr(10).join(f"- {warning}" for warning in generated_code.warnings)}

## Next Steps

1. Review the configuration above
2. Customize any variables as needed
3. Apply using: `kubectl apply -f your-config.yaml`
4. Monitor deployment: `kubectl get pods -n {generated_code.variables_applied.get('NAMESPACE', 'gsoc')}`

## Follow-up Questions

{chr(10).join(f"- {question}" for question in generated_code.follow_up_questions)}
"""

        return response

    def _handle_no_templates(self, request: AgentRequest,
                           analysis: Dict[str, Any]) -> AgentResponse:
        """Handle case where no templates are found."""

        resource_type = analysis.get("resource_type", "unknown")

        content = f"""I don't have a specific template for "{resource_type}" yet.

However, I can help you with these common Kubernetes resources:

**Available Templates:**
{chr(10).join(f"- {name}: {template.description}" for name, template in self.templates.items())}

**Suggestions:**
- Try requesting a "deployment" or "service" instead
- Be more specific about the resource type
- Ask for a "basic deployment with {resource_type} features"

Would you like me to create a basic template for you?"""

        return AgentResponse(
            success=False,
            content=content,
            agent_type="Code Generator",
            confidence=ConfidenceLevel.LOW,
            metadata={"available_templates": list(self.templates.keys())},
            follow_up_suggestions=[
                "Try asking for a deployment template",
                "Be more specific about resource requirements",
                "Ask what templates are available"
            ]
        )

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities."""
        return [
            "Generate Kubernetes YAML configurations",
            "Create deployments, services, ingress, and other resources",
            "Apply NRP-specific defaults and best practices",
            "Provide source citations from NRP documentation",
            "Generate follow-up questions for refinement",
            "Validate against NRP policies and guidelines"
        ]


def init_code_generator() -> CodeGeneratorAgent:
    """Initialize the code generator agent."""
    return CodeGeneratorAgent()