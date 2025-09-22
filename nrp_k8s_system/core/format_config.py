"""
Output Format Configuration

Provides configurable settings for the output formatter to make
the system truly modular and easily customizable.
"""

from typing import Dict, List, Any
import json
import os


class FormatConfig:
    """Configuration manager for output formatting"""

    DEFAULT_CONFIG = {
        "symbols": {
            "critical_warning": "🔴",
            "important_notice": "⚠️",
            "analysis_summary": "📋",
            "related_resources": "📚",
            "next_steps": "🎯",
            "success": "✅",
            "failure": "❌",
            "policy_requirements": "⚠️",
            "critical_restrictions": "🚨",
            "compliance_essentials": "💡",
            "understanding_check": "🎯",
            "yaml_config": "📝",
            "safety_validation": "🔒",
            "deployment_results": "🚀",
            "monitoring": "📚",
            "template_learning": "📖",
            "knowledge_response": "📖",
            "key_policies": "🔍",
            "practical_examples": "💡",
            "common_pitfalls": "⚠️",
            "cluster_operations": "⚡",
            "blocked_deployment": "🔴"
        },
        "colors": {
            "critical": "\033[91m",  # Red
            "warning": "\033[93m",   # Yellow
            "success": "\033[92m",   # Green
            "info": "\033[94m",      # Blue
            "reset": "\033[0m"       # Reset
        },
        "formatting": {
            "header_width": 53,
            "use_colors": False,  # Default to False for compatibility
            "box_chars": {
                "top_left": "┌",
                "top_right": "┐",
                "bottom_left": "└",
                "bottom_right": "┘",
                "horizontal": "─",
                "vertical": "│"
            }
        },
        "stage_names": {
            1: "Policy Education & Safety Briefing",
            2: "Compliant YAML Generation",
            3: "Kubernetes Deployment Execution"
        },
        "specialists": [
            "Security",
            "Template",
            "Policy",
            "Documentation",
            "Validation"
        ],
        "compliance_thresholds": {
            "minimum_confidence": 90,
            "minimum_compliance_score": 85,
            "risk_tolerance": "MEDIUM"
        },
        "output_sections": {
            "always_show": [
                "header",
                "analysis_summary",
                "next_steps"
            ],
            "conditional_show": [
                "warnings",
                "resources",
                "approval_prompt"
            ]
        }
    }

    def __init__(self, config_path: str = None):
        """Initialize configuration"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__),
            "..",
            "config",
            "output_format_config.json"
        )
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from file if it exists"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                self._merge_config(user_config)
            except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
                print(f"Warning: Could not load config from {self.config_path}: {e}")
                print("Using default configuration.")

    def save_config(self) -> None:
        """Save current configuration to file"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except (PermissionError, OSError) as e:
            print(f"Warning: Could not save config to {self.config_path}: {e}")

    def _merge_config(self, user_config: Dict[str, Any]) -> None:
        """Merge user configuration with defaults"""
        def merge_dict(default: Dict, user: Dict) -> Dict:
            result = default.copy()
            for key, value in user.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dict(result[key], value)
                else:
                    result[key] = value
            return result

        self.config = merge_dict(self.config, user_config)

    def get_symbol(self, symbol_name: str) -> str:
        """Get symbol for given name"""
        return self.config["symbols"].get(symbol_name, "•")

    def get_color(self, color_name: str) -> str:
        """Get color code if colors are enabled"""
        if self.config["formatting"]["use_colors"]:
            return self.config["colors"].get(color_name, "")
        return ""

    def get_stage_name(self, stage_number: int) -> str:
        """Get stage name for given number"""
        return self.config["stage_names"].get(stage_number, f"Stage {stage_number}")

    def get_specialists(self) -> List[str]:
        """Get list of available specialists"""
        return self.config["specialists"].copy()

    def get_compliance_threshold(self, threshold_name: str) -> Any:
        """Get compliance threshold value"""
        return self.config["compliance_thresholds"].get(threshold_name)

    def should_show_section(self, section_name: str, has_content: bool = True) -> bool:
        """Determine if a section should be shown"""
        if section_name in self.config["output_sections"]["always_show"]:
            return True
        if section_name in self.config["output_sections"]["conditional_show"]:
            return has_content
        return has_content

    def get_box_chars(self) -> Dict[str, str]:
        """Get box drawing characters"""
        return self.config["formatting"]["box_chars"].copy()

    def get_header_width(self) -> int:
        """Get header width"""
        return self.config["formatting"]["header_width"]

    def customize_symbol(self, symbol_name: str, new_symbol: str) -> None:
        """Customize a symbol"""
        self.config["symbols"][symbol_name] = new_symbol

    def enable_colors(self, enabled: bool = True) -> None:
        """Enable or disable color output"""
        self.config["formatting"]["use_colors"] = enabled

    def add_specialist(self, specialist_name: str) -> None:
        """Add a new specialist to the list"""
        if specialist_name not in self.config["specialists"]:
            self.config["specialists"].append(specialist_name)

    def export_config_template(self, output_path: str = None) -> str:
        """Export configuration template for customization"""
        template_path = output_path or "output_format_config_template.json"

        template_config = {
            "_comment": "NRP Kubernetes Agent Output Format Configuration",
            "_instructions": {
                "symbols": "Customize emoji/symbols used in output",
                "colors": "ANSI color codes (only used if use_colors is true)",
                "formatting": "Visual formatting options",
                "stage_names": "Names for the 3 workflow stages",
                "specialists": "Available specialist consultants",
                "compliance_thresholds": "Safety and compliance thresholds",
                "output_sections": "Control which sections are shown"
            },
            **self.config
        }

        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template_config, f, indent=2, ensure_ascii=False)

        return template_path


# Global configuration instance
format_config = FormatConfig()