from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str = ""
    GENIUS_ACCESS_TOKEN: str = ""
    SCRAPER_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./ksl.db"
    AI_MODEL: str = "claude-sonnet-4-20250514"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
