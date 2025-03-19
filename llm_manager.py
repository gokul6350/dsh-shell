import os
import platform
import google.generativeai as genai
from litellm import completion
import requests
import config

class LLMManager:
    def __init__(self):
        self.current_provider = config.DEFAULT_LLM_PROVIDER
        self.available_providers = ["gemini", "openai", "claude", "ollama"]
        self.model_configs = config.MODEL_SETTINGS
        self.available_models = {}
        
        # Initialize providers and fetch available models
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize providers and fetch their available models"""
        # Initialize Gemini
        if config.GEMINI_API_KEY != "your-api-key-here":
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel(
                model_name=self.model_configs["gemini"]["model_name"],
                generation_config=self.model_configs["gemini"]
            )
            self.available_models["gemini"] = ["gemini-pro", "gemini-pro-vision", "gemini-2.0-flash-exp"]
        
        # Fetch OpenAI models
        if config.OPENAI_API_KEY != "your-openai-api-key-here":
            self._fetch_openai_models()
        
        # Fetch Claude models
        if config.CLAUDE_API_KEY != "your-claude-api-key-here":
            self.available_models["claude"] = ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240229"]
        
        # Fetch Ollama models
        self._fetch_ollama_models()

    def _fetch_openai_models(self):
        """Fetch available models from OpenAI"""
        try:
            headers = {"Authorization": f"Bearer {config.OPENAI_API_KEY}"}
            response = requests.get("https://api.openai.com/v1/models", headers=headers)
            if response.status_code == 200:
                models = response.json()["data"]
                self.available_models["openai"] = [model["id"] for model in models 
                                                 if model["id"].startswith(("gpt-4", "gpt-3.5"))]
        except Exception as e:
            print(f"Error fetching OpenAI models: {e}")
            self.available_models["openai"] = ["gpt-4-turbo-preview", "gpt-4", "gpt-3.5-turbo"]

    def _fetch_ollama_models(self):
        """Fetch available models from Ollama"""
        try:
            response = requests.get(f"{config.OLLAMA_HOST}/api/tags")
            if response.status_code == 200:
                models = response.json()["models"]
                self.available_models["ollama"] = [model["name"] for model in models]
            else:
                self.available_models["ollama"] = ["llama2", "mistral", "codellama"]
        except Exception as e:
            print(f"Error fetching Ollama models: {e}")
            self.available_models["ollama"] = ["llama2", "mistral", "codellama"]

    def get_available_models(self, provider=None):
        """Get available models for a specific provider or all providers"""
        if provider:
            return self.available_models.get(provider, [])
        return self.available_models

    def switch_provider(self, provider_name):
        """Switch between different LLM providers"""
        if provider_name not in self.available_providers:
            raise ValueError(f"Provider {provider_name} not supported")
        self.current_provider = provider_name

    def get_available_providers(self):
        """Get list of available LLM providers"""
        return self.available_providers

    def update_model_config(self, provider, config_updates):
        """Update configuration for a specific provider's model"""
        if provider not in self.model_configs:
            raise ValueError(f"Provider {provider} not found")
        self.model_configs[provider].update(config_updates)

    async def generate_response(self, input_text):
        """Generate response using the current provider"""
        if self.current_provider == "gemini":
            response = self.gemini_model.generate_content(input_text)
            return response.text

        elif self.current_provider == "openai":
            response = await completion(
                model=self.model_configs["openai"]["model_name"],
                messages=[{"role": "user", "content": input_text}],
                temperature=self.model_configs["openai"]["temperature"],
                max_tokens=self.model_configs["openai"]["max_tokens"],
                api_key=config.OPENAI_API_KEY
            )
            return response.choices[0].message.content

        elif self.current_provider == "claude":
            response = await completion(
                model=self.model_configs["claude"]["model_name"],
                messages=[{"role": "user", "content": input_text}],
                temperature=self.model_configs["claude"]["temperature"],
                max_tokens=self.model_configs["claude"]["max_tokens"],
                api_key=config.CLAUDE_API_KEY
            )
            return response.choices[0].message.content

        elif self.current_provider == "ollama":
            response = await completion(
                model=f"ollama/{self.model_configs['ollama']['model_name']}",
                messages=[{"role": "user", "content": input_text}],
                temperature=self.model_configs["ollama"]["temperature"],
                max_tokens=self.model_configs["ollama"]["max_tokens"]
            )
            return response.choices[0].message.content

        raise ValueError(f"Provider {self.current_provider} not implemented")