"""
Prompt manager for AI interactions.

This module handles loading and rendering prompt templates from the prompt-templates/solar/
directory. See backend-structure.md for detailed specification.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class PromptManager:
    """Manages prompt templates for AI interactions."""
    
    def __init__(self, templates_dir: str = "prompt-templates/solar"):
        """
        Initialize prompt manager.
        
        Args:
            templates_dir: Directory containing prompt templates
        """
        self.templates_dir = Path(templates_dir)
        
    def load_prompt(self, prompt_name: str) -> tuple[str, Dict[str, Any]]:
        """
        Load prompt template and metadata.
        
        Args:
            prompt_name: Name of the prompt template (without extension)
            
        Returns:
            Tuple of (prompt_text, metadata)
        """
        prompt_file = self.templates_dir / f"{prompt_name}.prompt"
        meta_file = self.templates_dir / f"{prompt_name}.meta.yaml"
        
        # Load prompt text
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt template not found: {prompt_file}")
            
        with open(prompt_file, 'r') as f:
            prompt_text = f.read()
            
        # Load metadata
        metadata = {}
        if meta_file.exists():
            with open(meta_file, 'r') as f:
                metadata = yaml.safe_load(f) or {}
                
        return prompt_text, metadata
        
    def render_prompt(self, 
                     prompt_name: str, 
                     variables: Dict[str, Any]) -> str:
        """
        Render prompt template with variables.
        
        Args:
            prompt_name: Name of the prompt template
            variables: Variables to substitute in template
            
        Returns:
            Rendered prompt text
        """
        # TODO: Implement Jinja2 or simple templating
        # TODO: Add variable validation against metadata
        
        prompt_text, metadata = self.load_prompt(prompt_name)
        
        # Simple variable substitution for now
        rendered = prompt_text
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, str(value))
            
        return rendered
        
    def list_prompts(self) -> list[str]:
        """
        List available prompt templates.
        
        Returns:
            List of prompt template names
        """
        if not self.templates_dir.exists():
            return []
            
        prompts = []
        for file in self.templates_dir.glob("*.prompt"):
            prompts.append(file.stem)
            
        return prompts 