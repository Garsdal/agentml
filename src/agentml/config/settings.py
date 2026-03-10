"""Application settings — Pydantic Settings with YAML + env var support."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    """API server configuration."""

    host: str = "127.0.0.1"
    port: int = 8000


class LLMSettings(BaseSettings):
    """LLM provider configuration."""

    provider: str = "stub"
    model: str = "stub"
    api_key: str = ""


class SandboxSettings(BaseSettings):
    """Sandbox execution configuration."""

    timeout: float = 30.0


class StorageSettings(BaseSettings):
    """Storage configuration."""

    base_dir: Path = Path(".agentml")


class TrackingSettings(BaseSettings):
    """Experiment tracking configuration."""

    enabled: bool = True


class Settings(BaseSettings):
    """Root application settings.

    Loads from environment variables with AGENTML_ prefix,
    and from .agentml/config.yaml if present.
    """

    model_config = SettingsConfigDict(
        env_prefix="AGENTML_",
        env_nested_delimiter="__",
    )

    api: APISettings = Field(default_factory=APISettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    sandbox: SandboxSettings = Field(default_factory=SandboxSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    tracking: TrackingSettings = Field(default_factory=TrackingSettings)

    @classmethod
    def load(cls, config_path: Path | None = None) -> "Settings":
        """Load settings, optionally from a YAML config file.

        Args:
            config_path: Path to a YAML config file. Defaults to .agentml/config.yaml.

        Returns:
            Populated Settings instance.
        """
        import yaml

        path = config_path or Path(".agentml/config.yaml")
        if path.exists():
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)
        return cls()
