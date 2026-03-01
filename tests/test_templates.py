"""
Tests for prompt templates.
"""
import pytest
from pathlib import Path


EXPECTED_TEMPLATES = [
    "fix_grammar.j2",
    "summarize.j2",
    "deep_research.j2",
    "expand.j2",
]


def test_prompts_directory_exists(prompts_dir: Path):
    """Verify the prompts directory exists."""
    assert prompts_dir.exists(), f"Prompts directory not found at {prompts_dir}"


@pytest.mark.parametrize("template_name", EXPECTED_TEMPLATES)
def test_template_exists(prompts_dir: Path, template_name: str):
    """Verify each expected template file exists."""
    template_path = prompts_dir / template_name
    assert template_path.exists(), f"Template not found: {template_path}"


def test_template_has_text_variable(prompts_dir: Path):
    """Verify each template uses the {{ text }} variable."""
    for template_name in EXPECTED_TEMPLATES:
        template_path = prompts_dir / template_name
        content = template_path.read_text()
        assert "{{ text }}" in content, f"Template {template_name} missing {{{{ text }}}} variable"
