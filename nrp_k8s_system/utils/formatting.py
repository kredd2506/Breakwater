#!/usr/bin/env python3
"""
Output formatting utilities for NRP K8s System
"""

import json
import yaml
from typing import Any, Dict, List, Union, Optional
from datetime import datetime

def format_json_output(data: Any, indent: int = 2) -> str:
    """Format data as pretty JSON."""
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except TypeError:
        return str(data)

def format_yaml_output(data: Any) -> str:
    """Format data as YAML."""
    try:
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)
    except Exception:
        return str(data)

def format_table(headers: List[str], rows: List[List[str]],
                 max_col_width: int = 50) -> str:
    """Format data as a simple table."""
    if not headers or not rows:
        return "No data to display"

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    # Apply max width limit
    col_widths = [min(w, max_col_width) for w in col_widths]

    # Create separator
    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    # Format header
    result = [separator]
    header_row = "|" + "|".join(f" {h:<{w}} " for h, w in zip(headers, col_widths)) + "|"
    result.append(header_row)
    result.append(separator)

    # Format rows
    for row in rows:
        formatted_row = "|"
        for i, (cell, width) in enumerate(zip(row, col_widths)):
            cell_str = str(cell)[:width]  # Truncate if needed
            formatted_row += f" {cell_str:<{width}} |"
        result.append(formatted_row)

    result.append(separator)
    return "\n".join(result)

def format_timestamp(timestamp: Optional[datetime] = None) -> str:
    """Format timestamp for display."""
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def format_error_message(error: Exception, context: str = "") -> str:
    """Format error message for user display."""
    error_msg = f"Error: {str(error)}"
    if context:
        error_msg = f"{context} - {error_msg}"
    return error_msg

def format_warning_box(message: str, title: str = "WARNING") -> str:
    """Format a warning message in a box."""
    lines = message.split('\n')
    max_len = max(len(line) for line in lines + [title])
    width = min(max_len + 4, 80)

    result = []
    result.append("┌" + "─" * (width - 2) + "┐")
    result.append(f"│ {title:^{width - 4}} │")
    result.append("├" + "─" * (width - 2) + "┤")

    for line in lines:
        padded_line = f"│ {line:<{width - 4}} │"
        result.append(padded_line)

    result.append("└" + "─" * (width - 2) + "┘")
    return "\n".join(result)

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text with suffix if too long."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def format_size(size_bytes: int) -> str:
    """Format byte size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"