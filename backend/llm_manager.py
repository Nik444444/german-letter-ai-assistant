"""
Multi-LLM Provider Manager
Manages multiple LLM providers with automatic fallback and quota management
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProviderStatus(Enum):
    ACTIVE = "active"
    QUOTA_EXCEEDED = "quota_exceeded"
    ERROR = "error"
    DISABLED = "disabled"

@dataclass
class ProviderConfig:
    name: str
    api_key: str
    priority: int
    status: ProviderStatus
    max_requests_per_minute: int
    max_requests_per_day: int
    current_requests_minute: int
    current_requests_day: int
    last_reset_minute: datetime
    last_reset_day: datetime
    error_count: int
    last_error: Optional[str]
    last_success: Optional[datetime]

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.name = config.name
        
    @abstractmethod
    async def generate_content(self, prompt: str) -> str:
        """Generate content using the LLM provider"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass
    
    def can_make_request(self) -> bool:
        """Check if provider can make a request based on rate limits"""
        now = datetime.now()
        
        # Reset minute counter
        if now - self.config.last_reset_minute >= timedelta(minutes=1):
            self.config.current_requests_minute = 0
            self.config.last_reset_minute = now
            
        # Reset day counter
        if now - self.config.last_reset_day >= timedelta(days=1):
            self.config.current_requests_day = 0
            self.config.last_reset_day = now
            
        # Check limits
        if self.config.current_requests_minute >= self.config.max_requests_per_minute:
            return False
        if self.config.current_requests_day >= self.config.max_requests_per_day:
            return False
            
        return True
    
    def record_request(self):
        """Record a request"""
        self.config.current_requests_minute += 1
        self.config.current_requests_day += 1
        
    def record_success(self):
        """Record a successful request"""
        self.config.last_success = datetime.now()
        self.config.error_count = 0
        self.config.status = ProviderStatus.ACTIVE
        
    def record_error(self, error: str):
        """Record an error"""
        self.config.error_count += 1
        self.config.last_error = error
        
        if self.config.error_count >= 5:
            self.config.status = ProviderStatus.ERROR
            
class GeminiProvider(LLMProvider):
    """Google Gemini provider"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        try:
            import google.generativeai as genai
            if config.api_key and config.api_key != "your_gemini_api_key_here":
                genai.configure(api_key=config.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.genai = genai
            else:
                self.model = None
                logger.warning("Gemini API key not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.model = None
            
    async def generate_content(self, prompt: str) -> str:
        try:
            if not self.model:
                raise Exception("Gemini model not initialized")
                
            response = self.model.generate_content(prompt)
            
            if not response.text or response.text.strip() == "":
                raise Exception("Empty response from Gemini")
                
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            raise
            
    def is_available(self) -> bool:
        return self.model is not None and self.config.api_key and self.config.api_key not in ["your_gemini_api_key_here", ""]

class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        try:
            if config.api_key and config.api_key.startswith("sk-proj-"):
                import openai
                self.client = openai.OpenAI(api_key=config.api_key)
            else:
                self.client = None
                logger.warning("OpenAI API key not configured properly")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            self.client = None
            
    async def generate_content(self, prompt: str) -> str:
        try:
            if not self.client:
                raise Exception("OpenAI client not initialized")
                
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise
            
    def is_available(self) -> bool:
        return self.client is not None and self.config.api_key and self.config.api_key.startswith("sk-proj-")

class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        try:
            if config.api_key and config.api_key not in ["your_anthropic_api_key_here", ""]:
                import anthropic
                self.client = anthropic.Anthropic(api_key=config.api_key)
            else:
                self.client = None
                logger.warning("Anthropic API key not configured properly")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic: {e}")
            self.client = None
            
    async def generate_content(self, prompt: str) -> str:
        try:
            if not self.client:
                raise Exception("Anthropic client not initialized")
                
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            raise
            
    def is_available(self) -> bool:
        return self.client is not None and self.config.api_key and self.config.api_key not in ["your_anthropic_api_key_here", ""]

class OpenRouterProvider(LLMProvider):
    """OpenRouter provider"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        try:
            if config.api_key and config.api_key.startswith("sk-or-"):
                import openai
                self.client = openai.OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=config.api_key
                )
            else:
                self.client = None
                logger.warning("OpenRouter API key not configured properly")
        except Exception as e:
            logger.error(f"Failed to initialize OpenRouter: {e}")
            self.client = None
            
    async def generate_content(self, prompt: str) -> str:
        try:
            if not self.client:
                raise Exception("OpenRouter client not initialized")
                
            response = self.client.chat.completions.create(
                model="mistralai/mistral-7b-instruct:free",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenRouter error: {e}")
            raise
            
    def is_available(self) -> bool:
        return self.client is not None and self.config.api_key and self.config.api_key.startswith("sk-or-")

class CohereProvider(LLMProvider):
    """Cohere provider"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        try:
            if config.api_key and config.api_key not in ["your_cohere_api_key_here", ""]:
                import cohere
                self.client = cohere.Client(config.api_key)
            else:
                self.client = None
                logger.warning("Cohere API key not configured properly")
        except Exception as e:
            logger.error(f"Failed to initialize Cohere: {e}")
            self.client = None
            
    async def generate_content(self, prompt: str) -> str:
        try:
            if not self.client:
                raise Exception("Cohere client not initialized")
                
            response = self.client.generate(
                model="command-light",
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.generations[0].text.strip()
            
        except Exception as e:
            logger.error(f"Cohere error: {e}")
            raise
            
    def is_available(self) -> bool:
        return self.client is not None and self.config.api_key and self.config.api_key not in ["your_cohere_api_key_here", ""]

class MistralProvider(LLMProvider):
    """Mistral provider"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        try:
            if config.api_key and config.api_key not in ["your_mistral_api_key_here", ""]:
                import mistralai
                self.client = mistralai.Mistral(api_key=config.api_key)
            else:
                self.client = None
                logger.warning("Mistral API key not configured properly")
        except Exception as e:
            logger.error(f"Failed to initialize Mistral: {e}")
            self.client = None
            
    async def generate_content(self, prompt: str) -> str:
        try:
            if not self.client:
                raise Exception("Mistral client not initialized")
                
            response = self.client.chat.complete(
                model="mistral-tiny",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Mistral error: {e}")
            raise
            
    def is_available(self) -> bool:
        return self.client is not None and self.config.api_key and self.config.api_key not in ["your_mistral_api_key_here", ""]

class HuggingFaceProvider(LLMProvider):
    """Hugging Face provider"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if config.api_key and config.api_key not in ["your_huggingface_api_key_here", ""]:
            self.api_key = config.api_key
            self.base_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
        else:
            self.api_key = None
            logger.warning("Hugging Face API key not configured properly")
        
    async def generate_content(self, prompt: str) -> str:
        try:
            import requests
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            data = {"inputs": prompt}
            
            response = requests.post(self.base_url, headers=headers, json=data)
            
            if response.status_code != 200:
                raise Exception(f"HuggingFace API error: {response.status_code}")
                
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "").strip()
            else:
                raise Exception("Invalid response format from HuggingFace")
                
        except Exception as e:
            logger.error(f"HuggingFace error: {e}")
            raise
            
    def is_available(self) -> bool:
        return self.config.api_key and self.config.api_key not in ["your_huggingface_api_key_here", ""]

class MultiLLMManager:
    """Manages multiple LLM providers with automatic fallback"""
    
    def __init__(self):
        self.providers: List[LLMProvider] = []
        self.load_providers()
        
    def load_providers(self):
        """Load all available providers"""
        try:
            # Provider configurations
            provider_configs = {
                "gemini": ProviderConfig(
                    name="gemini",
                    api_key=os.getenv("GEMINI_API_KEY", ""),
                    priority=1,
                    status=ProviderStatus.ACTIVE,
                    max_requests_per_minute=15,
                    max_requests_per_day=1000,
                    current_requests_minute=0,
                    current_requests_day=0,
                    last_reset_minute=datetime.now(),
                    last_reset_day=datetime.now(),
                    error_count=0,
                    last_error=None,
                    last_success=None
                ),
                "openai": ProviderConfig(
                    name="openai",
                    api_key=os.getenv("OPENAI_API_KEY", ""),
                    priority=2,
                    status=ProviderStatus.ACTIVE,
                    max_requests_per_minute=3,
                    max_requests_per_day=100,
                    current_requests_minute=0,
                    current_requests_day=0,
                    last_reset_minute=datetime.now(),
                    last_reset_day=datetime.now(),
                    error_count=0,
                    last_error=None,
                    last_success=None
                ),
                "anthropic": ProviderConfig(
                    name="anthropic",
                    api_key=os.getenv("ANTHROPIC_API_KEY", ""),
                    priority=3,
                    status=ProviderStatus.ACTIVE,
                    max_requests_per_minute=5,
                    max_requests_per_day=200,
                    current_requests_minute=0,
                    current_requests_day=0,
                    last_reset_minute=datetime.now(),
                    last_reset_day=datetime.now(),
                    error_count=0,
                    last_error=None,
                    last_success=None
                ),
                "openrouter": ProviderConfig(
                    name="openrouter",
                    api_key=os.getenv("OPENROUTER_API_KEY", ""),
                    priority=4,
                    status=ProviderStatus.ACTIVE,
                    max_requests_per_minute=10,
                    max_requests_per_day=500,
                    current_requests_minute=0,
                    current_requests_day=0,
                    last_reset_minute=datetime.now(),
                    last_reset_day=datetime.now(),
                    error_count=0,
                    last_error=None,
                    last_success=None
                ),
                "cohere": ProviderConfig(
                    name="cohere",
                    api_key=os.getenv("COHERE_API_KEY", ""),
                    priority=5,
                    status=ProviderStatus.ACTIVE,
                    max_requests_per_minute=5,
                    max_requests_per_day=100,
                    current_requests_minute=0,
                    current_requests_day=0,
                    last_reset_minute=datetime.now(),
                    last_reset_day=datetime.now(),
                    error_count=0,
                    last_error=None,
                    last_success=None
                ),
                "mistral": ProviderConfig(
                    name="mistral",
                    api_key=os.getenv("MISTRAL_API_KEY", ""),
                    priority=6,
                    status=ProviderStatus.ACTIVE,
                    max_requests_per_minute=5,
                    max_requests_per_day=100,
                    current_requests_minute=0,
                    current_requests_day=0,
                    last_reset_minute=datetime.now(),
                    last_reset_day=datetime.now(),
                    error_count=0,
                    last_error=None,
                    last_success=None
                ),
                "huggingface": ProviderConfig(
                    name="huggingface",
                    api_key=os.getenv("HUGGINGFACE_API_KEY", ""),
                    priority=7,
                    status=ProviderStatus.ACTIVE,
                    max_requests_per_minute=10,
                    max_requests_per_day=1000,
                    current_requests_minute=0,
                    current_requests_day=0,
                    last_reset_minute=datetime.now(),
                    last_reset_day=datetime.now(),
                    error_count=0,
                    last_error=None,
                    last_success=None
                )
            }
            
            # Initialize providers
            provider_classes = {
                "gemini": GeminiProvider,
                "openai": OpenAIProvider,
                "anthropic": AnthropicProvider,
                "openrouter": OpenRouterProvider,
                "cohere": CohereProvider,
                "mistral": MistralProvider,
                "huggingface": HuggingFaceProvider
            }
            
            for name, config in provider_configs.items():
                try:
                    provider_class = provider_classes[name]
                    provider = provider_class(config)
                    if provider.is_available():
                        self.providers.append(provider)
                        logger.info(f"Successfully loaded provider: {name}")
                    else:
                        logger.warning(f"Provider {name} is not available (missing API key)")
                except Exception as e:
                    logger.error(f"Failed to load provider {name}: {e}")
                    
            # Sort providers by priority
            self.providers.sort(key=lambda p: p.config.priority)
            
            logger.info(f"Loaded {len(self.providers)} LLM providers")
            
        except Exception as e:
            logger.error(f"Failed to load providers: {e}")
            
    async def generate_content(self, prompt: str) -> Tuple[str, str]:
        """Generate content using available providers with fallback"""
        last_error = None
        
        for provider in self.providers:
            try:
                # Check if provider can make request
                if not provider.can_make_request():
                    logger.info(f"Provider {provider.name} has reached rate limit, skipping")
                    continue
                    
                # Check if provider is available
                if provider.config.status != ProviderStatus.ACTIVE:
                    logger.info(f"Provider {provider.name} is not active, skipping")
                    continue
                    
                logger.info(f"Attempting to use provider: {provider.name}")
                
                # Record request
                provider.record_request()
                
                # Generate content
                content = await provider.generate_content(prompt)
                
                # Record success
                provider.record_success()
                
                logger.info(f"Successfully generated content using {provider.name}")
                return content, provider.name
                
            except Exception as e:
                last_error = str(e)
                provider.record_error(last_error)
                logger.error(f"Provider {provider.name} failed: {e}")
                continue
                
        # If all providers failed
        error_msg = f"All LLM providers failed. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)
        
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {}
        for provider in self.providers:
            status[provider.name] = {
                "status": provider.config.status.value,
                "priority": provider.config.priority,
                "requests_today": provider.config.current_requests_day,
                "max_requests_day": provider.config.max_requests_per_day,
                "requests_this_minute": provider.config.current_requests_minute,
                "max_requests_minute": provider.config.max_requests_per_minute,
                "error_count": provider.config.error_count,
                "last_error": provider.config.last_error,
                "last_success": provider.config.last_success.isoformat() if provider.config.last_success else None,
                "can_make_request": provider.can_make_request()
            }
        return status

# Global instance
llm_manager = MultiLLMManager()