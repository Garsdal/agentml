"""Default configuration values."""

DEFAULTS = {
    "api": {
        "host": "127.0.0.1",
        "port": 8000,
    },
    "storage": {
        "base_dir": ".agentml",
    },
    "sandbox": {
        "timeout": 30.0,
    },
    "llm": {
        "provider": "stub",
        "model": "stub",
    },
    "tracking": {
        "enabled": True,
    },
}
