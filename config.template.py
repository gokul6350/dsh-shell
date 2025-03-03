# LLM API Configuration
# Rename this file to config.py and add your API keys

# Gemini API Configuration
GEMINI_API_KEY = "your-api-key-here"

# OpenAI API Configuration
OPENAI_API_KEY = "your-openai-api-key-here"

# Anthropic (Claude) API Configuration
CLAUDE_API_KEY = "your-claude-api-key-here"

# Ollama Configuration
# If using Ollama locally, set the host URL
OLLAMA_HOST = "http://localhost:11434"  # Default Ollama host

# LLM Provider Settings
DEFAULT_LLM_PROVIDER = "gemini"  # Options: "gemini", "openai", "claude", "ollama"

# Model Settings
MODEL_SETTINGS = {
    "gemini": {
        "model_name": "gemini-2.0-flash-exp",
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192
    },
    "openai": {
        "model_name": "gpt-4-turbo-preview",
        "temperature": 0.7,
        "max_tokens": 4096
    },
    "claude": {
        "model_name": "claude-3-opus-20240229",
        "temperature": 0.7,
        "max_tokens": 4096
    },
    "ollama": {
        "model_name": "llama2",  # Change to your preferred local model
        "temperature": 0.7,
        "max_tokens": 4096
    }
}

# Additional configuration settings
# DATABASE_URL = ""
# DEBUG = True