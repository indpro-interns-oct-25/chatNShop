"""
Prompt Loader for LLM Intent Classification

Loads and manages system prompts and few-shot examples with caching,
versioning, and error handling for production use.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from functools import lru_cache

from .confidence_calibrator import PROMPT_VERSION, validate_prompt_schema

logger = logging.getLogger("app.llm_intent.prompt_loader")

# Base directory for prompts
_PROMPTS_DIR = Path(__file__).parent / "prompts"


class PromptLoadError(Exception):
    """Raised when prompt files cannot be loaded."""
    pass


@lru_cache(maxsize=1)
def _load_system_prompt(version: str = PROMPT_VERSION) -> str:
    """
    Load system prompt from file with caching.
    
    Args:
        version: Prompt version (e.g., "v1.0.0")
        
    Returns:
        System prompt text
        
    Raises:
        PromptLoadError: If file cannot be loaded or doesn't exist
    """
    prompt_file = _PROMPTS_DIR / f"system_prompt_{version}.txt"
    
    if not prompt_file.exists():
        raise PromptLoadError(
            f"System prompt file not found: {prompt_file}. "
            f"Ensure prompts are in {_PROMPTS_DIR}"
        )
    
    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        
        if not content:
            raise PromptLoadError(f"System prompt file is empty: {prompt_file}")
        
        logger.info(f"Loaded system prompt from {prompt_file.name} (version: {version})")
        return content
        
    except IOError as e:
        raise PromptLoadError(f"Failed to read system prompt file: {e}") from e


@lru_cache(maxsize=1)
def _load_few_shot_examples(version: str = PROMPT_VERSION) -> List[Dict]:
    """
    Load few-shot examples from JSON file with caching.
    
    Args:
        version: Prompt version (e.g., "v1.0.0")
        
    Returns:
        List of few-shot example dictionaries
        
    Raises:
        PromptLoadError: If file cannot be loaded, parsed, or validated
    """
    examples_file = _PROMPTS_DIR / f"few_shot_examples_{version}.json"
    
    if not examples_file.exists():
        raise PromptLoadError(
            f"Few-shot examples file not found: {examples_file}. "
            f"Ensure prompts are in {_PROMPTS_DIR}"
        )
    
    try:
        with open(examples_file, "r", encoding="utf-8") as f:
            examples = json.load(f)
        
        if not isinstance(examples, list):
            raise PromptLoadError(
                f"Few-shot examples must be a list, got {type(examples)}"
            )
        
        if not examples:
            raise PromptLoadError(f"Few-shot examples file is empty: {examples_file}")
        
        # Validate schema
        try:
            validate_prompt_schema(examples)
        except ValueError as e:
            raise PromptLoadError(f"Few-shot examples schema validation failed: {e}") from e
        
        logger.info(
            f"Loaded {len(examples)} few-shot examples from {examples_file.name} "
            f"(version: {version})"
        )
        return examples
        
    except json.JSONDecodeError as e:
        raise PromptLoadError(f"Failed to parse JSON in few-shot examples: {e}") from e
    except IOError as e:
        raise PromptLoadError(f"Failed to read few-shot examples file: {e}") from e


class PromptLoader:
    """
    Production-ready prompt loader with caching, versioning, and error handling.
    
    Loads system prompts and few-shot examples, providing them in the format
    expected by OpenAI's ChatCompletion API.
    """
    
    def __init__(self, version: str = PROMPT_VERSION):
        """
        Initialize prompt loader.
        
        Args:
            version: Prompt version to load (default: from confidence_calibrator)
        """
        self.version = version
        self._system_prompt: Optional[str] = None
        self._few_shot_examples: Optional[List[Dict]] = None
        self._loaded = False
    
    def load(self) -> None:
        """Load system prompt and few-shot examples (idempotent)."""
        if self._loaded:
            return
        
        try:
            self._system_prompt = _load_system_prompt(self.version)
            self._few_shot_examples = _load_few_shot_examples(self.version)
            self._loaded = True
            logger.info(f"PromptLoader initialized with version {self.version}")
        except PromptLoadError as e:
            logger.error(f"Failed to load prompts: {e}")
            raise
    
    @property
    def system_prompt(self) -> str:
        """Get system prompt, loading if necessary."""
        if not self._loaded:
            self.load()
        if self._system_prompt is None:
            raise PromptLoadError("System prompt not loaded")
        return self._system_prompt
    
    @property
    def few_shot_examples(self) -> List[Dict]:
        """Get few-shot examples, loading if necessary."""
        if not self._loaded:
            self.load()
        if self._few_shot_examples is None:
            raise PromptLoadError("Few-shot examples not loaded")
        return self._few_shot_examples
    
    def build_messages(self, user_query: str) -> List[Dict[str, str]]:
        """
        Build message array for OpenAI ChatCompletion API.
        
        Format: [system, user1, assistant1, user2, assistant2, ..., user_query]
        
        Args:
            user_query: The actual user query to classify
            
        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        if not self._loaded:
            self.load()
        
        messages = []
        
        # Add system prompt
        messages.append({
            "role": "system",
            "content": self.system_prompt
        })
        
        # Add few-shot examples (user-assistant pairs)
        for example in self.few_shot_examples:
            messages.append({
                "role": "user",
                "content": example["user"]
            })
            # Format assistant response as JSON string
            assistant_content = json.dumps(example["assistant"], ensure_ascii=False)
            messages.append({
                "role": "assistant",
                "content": assistant_content
            })
        
        # Add actual user query
        messages.append({
            "role": "user",
            "content": user_query
        })
        
        return messages
    
    def reload(self) -> None:
        """Clear cache and reload prompts (useful for hot-reload in production)."""
        _load_system_prompt.cache_clear()
        _load_few_shot_examples.cache_clear()
        self._loaded = False
        self._system_prompt = None
        self._few_shot_examples = None
        self.load()
        logger.info(f"Prompts reloaded (version: {self.version})")
    
    def get_info(self) -> Dict[str, any]:
        """Get information about loaded prompts."""
        if not self._loaded:
            return {
                "loaded": False,
                "version": self.version
            }
        
        return {
            "loaded": True,
            "version": self.version,
            "system_prompt_length": len(self.system_prompt) if self._system_prompt else 0,
            "few_shot_examples_count": len(self.few_shot_examples) if self._few_shot_examples else 0,
        }


# Singleton instance for production use
_default_loader: Optional[PromptLoader] = None


def get_prompt_loader(version: str = PROMPT_VERSION) -> PromptLoader:
    """
    Get or create the default prompt loader singleton.
    
    Args:
        version: Prompt version (default: from confidence_calibrator)
        
    Returns:
        PromptLoader instance
    """
    global _default_loader
    if _default_loader is None or _default_loader.version != version:
        _default_loader = PromptLoader(version=version)
        _default_loader.load()
    return _default_loader


__all__ = ["PromptLoader", "PromptLoadError", "get_prompt_loader"]

