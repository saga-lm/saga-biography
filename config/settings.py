"""
Configuration management for SAGA Biography Generation System.
Handles environment variables and model configurations.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ConfigurationError(Exception):
    """Configuration related errors."""
    pass

class Settings:
    """Application configuration management."""
    
    def __init__(self):
        self._load_environment()
        self._validate_configuration()
    
    def _load_environment(self):
        """Load environment variables."""
        # Azure OpenAI Configuration
        self.azure_openai_api_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.azure_openai_api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
        
        # OpenRouter Configuration
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.openrouter_base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        
        # Private API Configuration
        self.private_api_key = os.getenv('PRIVATE_API_KEY')
        self.private_base_url_1 = os.getenv('PRIVATE_BASE_URL_1')
        self.private_base_url_2 = os.getenv('PRIVATE_BASE_URL_2')
        
        # Search API Configuration
        self.tavily_api_key = os.getenv('TAVILY_API_KEY')
        
        # Application Settings
        self.default_model = os.getenv('DEFAULT_MODEL', 'openai-gpt4')
        self.max_concurrent_workers = int(os.getenv('MAX_CONCURRENT_WORKERS', '10'))
        self.default_people_count = int(os.getenv('DEFAULT_PEOPLE_COUNT', '100'))
        
        # File system paths
        self.base_dir = Path(__file__).parent.parent
        self.results_dir = self.base_dir / "results"
        self.data_dir = self.base_dir / "data"
    
    def _validate_configuration(self):
        """Validate required configuration settings."""
        required_settings = []
        
        if not self.tavily_api_key:
            required_settings.append('TAVILY_API_KEY')
        
        # OpenRouter API key is required for all models
        if not self.openrouter_api_key:
            required_settings.append('OPENROUTER_API_KEY')
        
        if required_settings:
            raise ConfigurationError(f"Missing required configuration: {', '.join(required_settings)}")
    
    @property
    def model_configs(self) -> Dict[str, Any]:
        """Get all model configurations."""
        configs = {}
        
        # All models now use OpenRouter
        if self.openrouter_api_key:
            configs.update({
                "openai-o3": {
                    "type": "openai",
                    "model": "openai/o3",
                    "api_key": self.openrouter_api_key,
                    "base_url": self.openrouter_base_url,
                    "max_tokens": 4000,
                    "temperature": 1
                },
                "openai-gpt4": {
                    "type": "openai",
                    "model": "openai/gpt-4.1",
                    "api_key": self.openrouter_api_key,
                    "base_url": self.openrouter_base_url,
                    "max_tokens": 4000,
                    "temperature": 1
                },
                "claude-sonnet-4": {
                    "type": "openai",
                    "model": "anthropic/claude-sonnet-4",
                    "api_key": self.openrouter_api_key,
                    "base_url": self.openrouter_base_url,
                    "max_tokens": 4000,
                    "temperature": 1
                },
                "gemini-2.5-pro": {
                    "type": "openai",
                    "model": "google/gemini-2.5-pro",
                    "api_key": self.openrouter_api_key,
                    "base_url": self.openrouter_base_url,
                    "max_tokens": 4000,
                    "temperature": 1
                },
                "deepseek-r1": {
                    "type": "openai",
                    "model": "deepseek/deepseek-r1-0528",
                    "api_key": self.openrouter_api_key,
                    "base_url": self.openrouter_base_url,
                    "max_tokens": 4000,
                    "temperature": 1
                }
            })
        
        # Private endpoints
        if self.private_api_key:
            if self.private_base_url_1:
                configs.update({
                    "claude-sonnet-4-private": {
                        "type": "openai",
                        "model": "claude-sonnet-4-20250514",
                        "api_key": self.private_api_key,
                        "base_url": self.private_base_url_1,
                        "max_tokens": 4000,
                        "temperature": 1
                    },
                    "gemini-2.5-pro-private": {
                        "type": "openai",
                        "model": "gemini-2.5-pro",
                        "api_key": self.private_api_key,
                        "base_url": self.private_base_url_1,
                        "max_tokens": 4000,
                        "temperature": 1
                    }
                })
            
            if self.private_base_url_2:
                configs["deepseek-r1-private"] = {
                    "type": "openai",
                    "model": "deepseek-r1-250528",
                    "api_key": self.private_api_key,
                    "base_url": self.private_base_url_2,
                    "max_tokens": 4000,
                    "temperature": 1
                }
        
        return configs
    
    @property
    def model_backup_map(self) -> Dict[str, str]:
        """Get model backup mapping."""
        return {
            "claude-sonnet-4": "claude-sonnet-4-private",
            "gemini-2.5-pro": "gemini-2.5-pro-private",
            "deepseek-r1": "deepseek-r1-private"
        }
    
    def get_available_models(self) -> list:
        """Get list of available models."""
        return list(self.model_configs.keys())
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a model is available."""
        return model_name in self.model_configs

# Global settings instance
settings = Settings()