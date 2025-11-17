"""
Model client management for SAGA Biography Generation System.
Handles model client creation, fallback mechanisms, and retries.
"""

import asyncio
from typing import Dict, Any, Optional
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient, OpenAIChatCompletionClient
from config.settings import settings

class ModelClientError(Exception):
    """Model client related errors."""
    pass

class FallbackModelClient:
    """Model client with fallback functionality and retry mechanism."""
    
    def __init__(self, primary_model_name: str):
        self.primary_model_name = primary_model_name
        self.backup_model_name = settings.model_backup_map.get(primary_model_name)
        self._closed = False
        
        # Create primary client
        self.primary_client = self._create_single_client(primary_model_name)
        
        # Create backup client if available
        self.backup_client = None
        if self.backup_model_name and settings.is_model_available(self.backup_model_name):
            try:
                self.backup_client = self._create_single_client(self.backup_model_name)
                print(f"✅ Backup model configured for {primary_model_name}: {self.backup_model_name}")
            except Exception as e:
                print(f"⚠️ Backup model {self.backup_model_name} configuration failed: {e}")
    
    def _create_single_client(self, model_name: str):
        """Create a single model client."""
        if not settings.is_model_available(model_name):
            raise ValueError(f"Unknown model: {model_name}")
        
        config = settings.model_configs[model_name]
        
        if config["type"] == "azure":
            return AzureOpenAIChatCompletionClient(
                model=config["model"],
                api_key=config["api_key"],
                azure_endpoint=config["azure_endpoint"],
                api_version=config["api_version"]
            )
        elif config["type"] == "openai":
            return OpenAIChatCompletionClient(
                model=config["model"],
                api_key=config["api_key"],
                base_url=config["base_url"],
                model_capabilities={
                    "vision": False,
                    "function_calling": True,
                    "json_output": True
                }
            )
        else:
            raise ValueError(f"Unsupported model type: {config['type']}")
    
    async def create(self, **kwargs):
        """Create response with automatic fallback and retry mechanism."""
        # Try primary model first (with retries)
        for attempt in range(3):  # Maximum 3 retries
            try:
                response = await self.primary_client.create(**kwargs)
                return response
            except Exception as primary_error:
                error_msg = str(primary_error)
                
                # Check for event loop errors
                if "different event loop" in error_msg:
                    print(f"🔄 Event loop error detected, recreating client...")
                    try:
                        self.primary_client = self._create_single_client(self.primary_model_name)
                        await asyncio.sleep(1)
                        continue
                    except Exception:
                        pass
                
                # Log error on final attempt
                if attempt == 2:  # Last attempt
                    print(f"⚠️ Primary model {self.primary_model_name} failed: {error_msg[:100]}...")
                    break
                else:
                    print(f"🔄 Primary model attempt {attempt+1} failed, retrying in 1 second...")
                    await asyncio.sleep(1)
        
        # Try backup model if available
        if self.backup_client:
            for attempt in range(3):  # Backup model also gets 3 retries
                try:
                    print(f"🔄 Switching to backup model {self.backup_model_name}...")
                    response = await self.backup_client.create(**kwargs)
                    print(f"✅ Backup model {self.backup_model_name} response successful")
                    return response
                except Exception as backup_error:
                    error_msg = str(backup_error)
                    
                    # Check for event loop errors
                    if "different event loop" in error_msg:
                        print(f"🔄 Backup model event loop error, recreating client...")
                        try:
                            self.backup_client = self._create_single_client(self.backup_model_name)
                            await asyncio.sleep(1)
                            continue
                        except Exception:
                            pass
                    
                    if attempt == 2:  # Last attempt
                        print(f"❌ Backup model {self.backup_model_name} also failed: {error_msg[:100]}...")
                        # Both models failed, raise original error
                        raise Exception(f"Primary and backup models failed. Primary: {str(primary_error)[:100]}, Backup: {error_msg[:100]}")
                    else:
                        print(f"🔄 Backup model attempt {attempt+1} failed, retrying in 1 second...")
                        await asyncio.sleep(1)
        else:
            # No backup model, raise primary model error
            raise primary_error
    
    async def close(self):
        """Safely close all client connections."""
        errors = []
        
        # Close primary client
        if hasattr(self.primary_client, 'close'):
            try:
                await self.primary_client.close()
            except Exception as e:
                error_msg = str(e)
                if "event loop" not in error_msg.lower():
                    print(f"⚠️ Error closing primary client: {e}")
                errors.append(f"Primary client: {e}")
        
        # Close backup client
        if self.backup_client and hasattr(self.backup_client, 'close'):
            try:
                await self.backup_client.close()
            except Exception as e:
                error_msg = str(e)
                if "event loop" not in error_msg.lower():
                    print(f"⚠️ Error closing backup client: {e}")
                errors.append(f"Backup client: {e}")
        
        # Mark as closed
        self._closed = True
        
        # Log non-event-loop related errors
        if errors:
            print(f"⚠️ Client closure encountered errors: {errors}")
    
    def __del__(self):
        """Destructor to ensure resource cleanup."""
        if not getattr(self, '_closed', True):
            try:
                print(f"⚠️ FallbackModelClient {self.primary_model_name} not properly closed")
            except:
                pass

class ModelClientManager:
    """Manages model client creation and lifecycle."""
    
    def __init__(self):
        self._current_model = settings.default_model
        self._current_client = None
    
    def create_client(self, model_name: Optional[str] = None):
        """Create a model client with appropriate fallback configuration."""
        if model_name is None:
            model_name = self._current_model
        
        if not settings.is_model_available(model_name):
            print(f"⚠️ Unknown model: {model_name}, using default model {self._current_model}")
            model_name = self._current_model
        
        # If model has backup options, use FallbackModelClient
        if model_name in settings.model_backup_map:
            return FallbackModelClient(model_name)
        
        # No backup options available, use regular client
        config = settings.model_configs[model_name]
        
        if config["type"] == "azure":
            return AzureOpenAIChatCompletionClient(
                model=config["model"],
                api_key=config["api_key"],
                azure_endpoint=config["azure_endpoint"],
                api_version=config["api_version"]
            )
        elif config["type"] == "openai":
            return OpenAIChatCompletionClient(
                model=config["model"],
                api_key=config["api_key"],
                base_url=config["base_url"],
                model_capabilities={
                    "vision": False,
                    "function_calling": True,
                    "json_output": True
                }
            )
        else:
            raise ValueError(f"Unsupported model type: {config['type']}")
    
    def set_model(self, model_name: str) -> bool:
        """Set the global model to use."""
        if settings.is_model_available(model_name):
            self._current_model = model_name
            self._current_client = self.create_client(model_name)
            print(f"✅ Switched to model: {model_name} ({settings.model_configs[model_name]['model']})")
            return True
        else:
            print(f"❌ Unknown model: {model_name}")
            print(f"Available models: {settings.get_available_models()}")
            return False
    
    def list_models(self):
        """List all available models."""
        print("\n📋 Available models:")
        for name, config in settings.model_configs.items():
            current_mark = " ← Current" if name == self._current_model else ""
            print(f"  - {name}: {config['model']} ({config['type']}){current_mark}")
        print()
    
    @property
    def current_model(self) -> str:
        """Get the current model name."""
        return self._current_model
    
    @property
    def current_client(self):
        """Get the current model client."""
        if self._current_client is None:
            self._current_client = self.create_client()
        return self._current_client

# Global model client manager
model_manager = ModelClientManager()