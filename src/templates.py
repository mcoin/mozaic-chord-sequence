"""
Template management for Mozaic script generation.

This module provides the TemplateManager class for loading and rendering
Jinja2 templates for Mozaic scripts.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound


class TemplateManager:
    """
    Manages loading and rendering of Mozaic script templates.

    The TemplateManager uses Jinja2 for template rendering, providing a clean
    separation between the Mozaic script structure and the Python code.

    Attributes:
        template_dir: Directory containing template files
        env: Jinja2 Environment for template loading
    """

    def __init__(self, template_dir: Optional[Union[Path, str]] = None):
        """
        Initialize the TemplateManager.

        Args:
            template_dir: Path to directory containing templates.
                         Defaults to 'templates/' in project root.
        """
        if template_dir is None:
            # Default to templates/ directory in project root
            project_root = Path(__file__).parent.parent
            template_dir = project_root / "templates"

        self.template_dir = Path(template_dir)

        if not self.template_dir.exists():
            raise FileNotFoundError(
                f"Template directory not found: {self.template_dir}"
            )

        # Create Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

    def load_template(self, template_name: str) -> Template:
        """
        Load a template by name.

        Args:
            template_name: Name of the template file (e.g., 'chord_sequence.mozaic.j2')

        Returns:
            Jinja2 Template object

        Raises:
            TemplateNotFound: If the template file doesn't exist
        """
        try:
            return self.env.get_template(template_name)
        except TemplateNotFound as e:
            raise FileNotFoundError(
                f"Template '{template_name}' not found in {self.template_dir}"
            ) from e

    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with the given context.

        Args:
            template_name: Name of the template file
            context: Dictionary of variables to pass to the template

        Returns:
            Rendered template as a string

        Example:
            >>> manager = TemplateManager()
            >>> context = {'songs': [{'title': 'Test', 'num_bars': 4}]}
            >>> script = manager.render('chord_sequence.mozaic.j2', context)
        """
        template = self.load_template(template_name)
        return template.render(**context)

    def render_from_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        Render a template from a string (not a file).

        Useful for testing or dynamic template generation.

        Args:
            template_string: Template content as a string
            context: Dictionary of variables to pass to the template

        Returns:
            Rendered template as a string
        """
        template = self.env.from_string(template_string)
        return template.render(**context)

    def list_templates(self) -> List[str]:
        """
        List all available templates.

        Returns:
            List of template filenames
        """
        return self.env.list_templates()


# Convenience function for quick rendering
def render_chord_sequence(songs: List[Dict[str, Any]]) -> str:
    """
    Render the chord sequence template with the given songs.

    This is a convenience function that creates a TemplateManager and renders
    the default chord sequence template.

    Args:
        songs: List of song dictionaries with keys:
              - title: Song title
              - num_bars: Number of bars
              - tempo: Optional tempo in BPM
              - update_block: Mozaic script block for updating chords

    Returns:
        Rendered Mozaic script as a string

    Example:
        >>> songs = [
        ...     {
        ...         'title': 'Test Song',
        ...         'num_bars': 4,
        ...         'tempo': 120,
        ...         'update_block': '@UpdateChordsSong0\\n@End'
        ...     }
        ... ]
        >>> script = render_chord_sequence(songs)
    """
    manager = TemplateManager()
    return manager.render('chord_sequence.mozaic.j2', {'songs': songs})
