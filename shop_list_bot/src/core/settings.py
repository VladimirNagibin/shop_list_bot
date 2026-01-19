"""Application settings configuration using Pydantic."""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # type: ignore[misc]
    """Application settings loaded from environment variables and .env file."""

    BASE_DIR: str = Field(
        default_factory=lambda: str(Path(__file__).resolve().parent.parent),
        description="Base directory of the project",
    )

    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    LOGGING_FILE_MAX_BYTES: int = Field(
        default=500_000,
        ge=100_000,
        le=10_000_000,
        description="Maximum size of log file in bytes before rotation",
    )

    # Bot token from @BotFather
    BOT_TOKEN: str = Field(
        default="bot_token_here",
        min_length=10,
        description="Telegram bot token obtained from @BotFather",
    )

    DB_SQLITE_FILE: str = Field(
        default="data/shopping_cart.db",
        min_length=1,
        description="DB path for SQLite database",
    )

    @property
    def DB_SQLITE_PATH(self) -> Path:
        return Path(self.BASE_DIR) / self.DB_SQLITE_FILE

    POOL_SIZE: int = Field(
        default=1,
        gt=0,
        description="Pool size for database connections",
    )

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that LOG_LEVEL is a valid logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            error_message = f"LOG_LEVEL must be one of {valid_levels}"
            raise ValueError(error_message)
        return v.upper()

    @field_validator("BOT_TOKEN")
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """Validate that BOT_TOKEN has correct format."""
        if not v.startswith("bot"):
            error_message = 'BOT_TOKEN must start with "bot"'
            raise ValueError(error_message)
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="SHOP_BOT_",
    )


settings = Settings()
