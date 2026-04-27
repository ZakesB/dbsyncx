import yaml
from pathlib import Path
from typing import Dict, Any

from .exceptions import ConfigError


CONFIG_DIR = Path(".dbsyncx")
CONFIG_FILE = CONFIG_DIR / "config.yaml"


DEFAULT_CONFIG = {
    "project_id": "local-project",
    "databases": {
        "local": {
            "url": "postgresql://postgres:postgres@localhost:5432/postgres"
        }
    },
}


def init_config() -> None:
    """
    Initialize config directory and file.
    """
    CONFIG_DIR.mkdir(exist_ok=True)

    if CONFIG_FILE.exists():
        raise ConfigError("Config already exists at .dbsyncx/config.yaml")

    with open(CONFIG_FILE, "w") as f:
        yaml.dump(DEFAULT_CONFIG, f, sort_keys=False)


def load_config() -> Dict[str, Any]:
    """
    Load config from file.
    """
    if not CONFIG_FILE.exists():
        raise ConfigError("Config not found. Run: dbsyncx init")

    try:
        with open(CONFIG_FILE) as f:
            return yaml.safe_load(f)
    except yaml.YAMLError:
        raise ConfigError("Invalid YAML in config file")


def get_database_url(config: Dict[str, Any], name: str) -> str:
    """
    Get database URL by name.
    """
    try:
        return config["databases"][name]["url"]
    except KeyError:
        raise ConfigError(f"Database '{name}' not found in config")