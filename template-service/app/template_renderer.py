"""Template rendering with variable substitution"""
from jinja2 import Template, TemplateSyntaxError, UndefinedError
from typing import Dict, Any
import re

def render_template(template_string: str, variables: Dict[str, Any]) -> str:
    """
    Render a template string with provided variables.
    
    Supports both {{variable}} and {variable} syntax.
    Uses Jinja2 for advanced rendering capabilities.
    
    Args:
        template_string: Template string with variables
        variables: Dictionary of variable names and values
    
    Returns:
        Rendered string with variables replaced
    
    Raises:
        TemplateSyntaxError: If template syntax is invalid
        UndefinedError: If required variable is missing
    """
    if not template_string:
        return ""
    
    # First, convert simple {variable} syntax to {{variable}} for Jinja2
    # Only convert if they're not already double braces
    pattern = r'(?<!\{)\{(?!\{)([^{}]+)\}(?!\})'
    template_string = re.sub(pattern, r'{{\1}}', template_string)
    
    try:
        template = Template(template_string)
        return template.render(**variables)
    except (TemplateSyntaxError, UndefinedError) as e:
        raise Exception(f"Template rendering error: {str(e)}")

def extract_variables(template_string: str) -> list:
    """
    Extract all variable names from a template string.
    
    Args:
        template_string: Template string with variables
    
    Returns:
        List of unique variable names
    """
    if not template_string:
        return []
    
    # Find both {{variable}} and {variable} patterns
    pattern = r'\{\{?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}?\}'
    matches = re.findall(pattern, template_string)
    
    return list(set(matches))
