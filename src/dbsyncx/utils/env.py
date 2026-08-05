"""
Environment variable interpolation utilities.
"""

import os
import re
from typing import Any

from dbsyncx.exceptions import DbSyncXError


# Matches:
#   ${VAR}
#   ${VAR:default}
_ENV_PATTERN = re.compile(
    r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?::(?P<default>[^}]*))?\}"
)


def interpolate_env(value: str) -> str:
    """
    Replace environment variable placeholders in a string.

    Supported syntax:

        ${VAR}
        ${VAR:default}

    Raises:
        DbSyncXError: If a required environment variable is not defined.
    """

    def replace(match: re.Match) -> str:
        name = match.group("name")
        default = match.group("default")

        env_value = os.getenv(name)

        if env_value is not None:
            return env_value

        if default is not None:
            return default

        raise DbSyncXError(
            f"Environment variable '{name}' is not set."
        )

    return _ENV_PATTERN.sub(replace, value)

def interpolate(value: Any) -> Any:
    """
    Recursively interpolate environment variables.

    Supports dictionaries, lists and strings.
    """

    if isinstance(value, dict):
        return {
            key: interpolate(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            interpolate(item)
            for item in value
        ]

    if isinstance(value, str):
        return interpolate_env(value)

    return value