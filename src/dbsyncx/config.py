import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional

from .exceptions import ConfigError


CONFIG_DIR = Path(".dbsyncx")
CONFIG_FILE = CONFIG_DIR / "config.yaml"
CONFIG_FILE_ALT = CONFIG_DIR / "config.yml"


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

def resolve_config_path(cli_config: Optional[str] = None) -> Path:
    """
    Resolve config path
    """

    # 1. CLI flag
    if cli_config:
        path = Path(cli_config)
        if path.exists():
            return path
        raise FileNotFoundError(f"Config not found at: {path}")

    # 2. ENV variable
    env_config = os.getenv("DBSYNCX_CONFIG")
    if env_config:
        path = Path(env_config)
        if path.exists():
            return path
        raise FileNotFoundError(f"Config not found at: {path}")

    # 3. Local project config
    for filename in ("config.yaml", "config.yml"):
        local_path = Path.cwd() / ".dbsyncx" / filename
        if local_path.exists():
            return local_path

    # 4. Home directory fallback
    for filename in ("config.yaml", "config.yml"):
        home_path = Path.home() / ".dbsyncx" / filename
        if home_path.exists():
            return home_path

    raise FileNotFoundError(
        "Config not found. Use --config or set DBSYNCX_CONFIG"
    )

def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load config from file.
    """
    if not config_path.exists():
        raise ConfigError(f"Config not found at: {config_path}")

    try:
        with open(config_path) as f:
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
