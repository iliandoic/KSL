from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str = ""
    GENIUS_ACCESS_TOKEN: str = ""
    DATABASE_URL: str = "sqlite:///./ksl.db"
    AI_MODEL: str = "claude-haiku-4-5-20251001"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
