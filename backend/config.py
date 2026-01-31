from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    ollama_device_a_url: str = "http://localhost:11434"
    ollama_device_b_url: str = "http://localhost:11434"
    log_level: str = "INFO"

    # Model role → Ollama model name mapping.
    # These are the names created via `ollama create`.
    # Change the FROM line in the Modelfiles, not these strings.
    MODEL_MAIN_REASONER: str = "main-reasoner"
    MODEL_GRAPH_BUILDER: str = "graph-builder"

    # Context window limits (must match Modelfile num_ctx)
    CTX_MAIN_REASONER: int = 8192
    CTX_GRAPH_BUILDER: int = 4096

    # How many recent messages the chat agent sees
    CHAT_RECENT_MESSAGES: int = 10

    class Config:
        env_file = ".env"

settings = Settings()

# Device routing: which URL serves which model
DEVICE_URLS = {
    settings.MODEL_MAIN_REASONER: settings.ollama_device_a_url,
    settings.MODEL_GRAPH_BUILDER: settings.ollama_device_b_url,
}
