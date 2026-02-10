from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str

    # Auth settings
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24

    # LLM provider settings
    # Supported:
    # - ollama (local)
    # - openai
    # - anthropic
    # - gemini
    # - deepseek
    # - kimi
    # - openai_compatible (custom endpoint)
    llm_provider: str = "openai"

    # Generic cloud LLM config (used by provider adapters)
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_main_model: str | None = None
    llm_graph_model: str | None = None
    llm_timeout_seconds: float = 90.0

    # OpenAI-compatible auth customization for non-standard gateways
    llm_api_key_header: str = "Authorization"
    llm_api_key_prefix: str = "Bearer "

    # Anthropic-specific version header
    anthropic_version: str = "2023-06-01"

    # Backward-compatible Ollama routing
    ollama_device_a_url: str = "http://localhost:11434"
    ollama_device_b_url: str = "http://localhost:11434"

    # Model role names (for Ollama mode)
    MODEL_MAIN_REASONER: str = "main-reasoner"
    MODEL_GRAPH_BUILDER: str = "graph-builder"

    # Context window limits
    CTX_MAIN_REASONER: int = 8192
    CTX_GRAPH_BUILDER: int = 4096

    # How many recent messages the chat agent sees
    CHAT_RECENT_MESSAGES: int = 10

    # Context optimization controls
    INHERITED_FACT_LIMIT: int = 40
    INHERITED_DECISION_LIMIT: int = 25
    INHERITED_QUESTION_LIMIT: int = 10

    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()

# Device routing: which URL serves which model (Ollama mode)
DEVICE_URLS = {
    settings.MODEL_MAIN_REASONER: settings.ollama_device_a_url,
    settings.MODEL_GRAPH_BUILDER: settings.ollama_device_b_url,
}
