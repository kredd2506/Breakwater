import json
import yaml
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastmcp import FastMCP
from pydantic import BaseModel

class DataFormatter:
    """Enhanced data formatter with multiple output formats and serialization options"""

    @staticmethod
    def format_yaml(data: Any, indent: int = 2, sort_keys: bool = True) -> str:
        """Format data as YAML with custom options"""
        return yaml.dump(
            data,
            indent=indent,
            sort_keys=sort_keys,
            default_flow_style=False,
            allow_unicode=True
        )

    @staticmethod
    def format_json(data: Any, indent: int = 2, sort_keys: bool = True) -> str:
        """Format data as JSON with custom options"""
        return json.dumps(
            data,
            indent=indent,
            sort_keys=sort_keys,
            ensure_ascii=False,
            default=str
        )

    @staticmethod
    def add_metadata(data: Any, metadata: Optional[Dict] = None) -> Dict:
        """Add metadata to data before serialization"""
        if metadata is None:
            metadata = {}

        return {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "format_version": "1.0",
                "source": "FastMCP Enhanced Server",
                **metadata
            },
            "data": data
        }

# Create the enhanced MCP server
mcp = FastMCP(
    name="Enhanced Data Formatter Server",
    instructions="This server provides advanced data formatting, serialization, and transformation capabilities with YAML, JSON, and metadata support."
)

@mcp.tool
def format_data_yaml(
    data: Dict[str, Any],
    indent: int = 2,
    sort_keys: bool = True,
    add_metadata: bool = True
) -> str:
    """
    Format data as YAML with customizable options.

    Args:
        data: The data to format
        indent: Number of spaces for indentation (default: 2)
        sort_keys: Whether to sort keys alphabetically (default: True)
        add_metadata: Whether to add metadata wrapper (default: True)

    Returns:
        YAML formatted string
    """
    formatter = DataFormatter()

    if add_metadata:
        data = formatter.add_metadata(data, {"format": "yaml"})

    return formatter.format_yaml(data, indent=indent, sort_keys=sort_keys)

@mcp.tool
def format_data_json(
    data: Dict[str, Any],
    indent: int = 2,
    sort_keys: bool = True,
    add_metadata: bool = True
) -> str:
    """
    Format data as JSON with customizable options.

    Args:
        data: The data to format
        indent: Number of spaces for indentation (default: 2)
        sort_keys: Whether to sort keys alphabetically (default: True)
        add_metadata: Whether to add metadata wrapper (default: True)

    Returns:
        JSON formatted string
    """
    formatter = DataFormatter()

    if add_metadata:
        data = formatter.add_metadata(data, {"format": "json"})

    return formatter.format_json(data, indent=indent, sort_keys=sort_keys)

@mcp.tool
def transform_data(
    data: Dict[str, Any],
    transformations: List[str] = None
) -> Dict[str, Any]:
    """
    Apply transformations to data before formatting.

    Args:
        data: The data to transform
        transformations: List of transformation types ["uppercase_keys", "lowercase_keys", "remove_nulls", "flatten"]

    Returns:
        Transformed data dictionary
    """
    if transformations is None:
        transformations = []

    result = data.copy()

    for transform in transformations:
        if transform == "uppercase_keys":
            result = {k.upper(): v for k, v in result.items()}
        elif transform == "lowercase_keys":
            result = {k.lower(): v for k, v in result.items()}
        elif transform == "remove_nulls":
            result = {k: v for k, v in result.items() if v is not None}
        elif transform == "flatten":
            result = _flatten_dict(result)

    return result

def _flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

@mcp.tool
def create_structured_report(
    title: str,
    data: Dict[str, Any],
    format_type: str = "yaml",
    include_summary: bool = True
) -> str:
    """
    Create a structured report with title, summary, and formatted data.

    Args:
        title: Report title
        data: The data to include in the report
        format_type: Output format ("yaml" or "json")
        include_summary: Whether to include data summary

    Returns:
        Formatted report string
    """
    formatter = DataFormatter()

    report_data = {
        "title": title,
        "generated_at": datetime.now().isoformat(),
    }

    if include_summary:
        report_data["summary"] = {
            "total_keys": len(data) if isinstance(data, dict) else 1,
            "data_type": type(data).__name__,
            "has_nested_objects": any(isinstance(v, (dict, list)) for v in data.values()) if isinstance(data, dict) else False
        }

    report_data["content"] = data

    if format_type.lower() == "yaml":
        return formatter.format_yaml(report_data)
    else:
        return formatter.format_json(report_data)

@mcp.resource("config://server")
def get_server_config() -> Dict[str, Any]:
    """Get server configuration and capabilities"""
    return {
        "name": "Enhanced Data Formatter Server",
        "version": "1.0.0",
        "capabilities": [
            "YAML formatting",
            "JSON formatting",
            "Data transformation",
            "Metadata injection",
            "Structured reporting"
        ],
        "supported_formats": ["yaml", "json"],
        "transformations": [
            "uppercase_keys",
            "lowercase_keys",
            "remove_nulls",
            "flatten"
        ]
    }

@mcp.resource("examples://formatting")
def get_formatting_examples() -> Dict[str, Any]:
    """Get examples of data formatting capabilities"""
    return {
        "sample_data": {
            "user": {
                "name": "John Doe",
                "age": 30,
                "email": "john@example.com",
                "preferences": {
                    "theme": "dark",
                    "notifications": True
                }
            },
            "settings": {
                "language": "en",
                "timezone": "UTC"
            }
        },
        "transformation_examples": {
            "original": {"UserName": "John", "userAge": None, "UserEmail": "john@example.com"},
            "uppercase_keys": {"USERNAME": "John", "USERAGE": None, "USEREMAIL": "john@example.com"},
            "remove_nulls": {"UserName": "John", "UserEmail": "john@example.com"},
            "combined": {"USERNAME": "John", "USEREMAIL": "john@example.com"}
        }
    }

if __name__ == "__main__":
    # Run the server on HTTP transport
    mcp.run(transport="http", host="localhost", port=8001)