import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .base import DatabaseAdapter
from ..exceptions import AdapterError


@dataclass
class RestoreConfig:
    input_file: str
    clean: bool = False
    jobs: Optional[int] = None


class PostgresAdapter(DatabaseAdapter):
    """
    PostgreSQL adapter using pg_dump / pg_restore / psql
    """

    def dump(
        self,
        url: str,
        output_file: str,
        schema_only: bool = False,
        tables: Optional[List[str]] = None,
    ):
        cmd = ["pg_dump", url, "-Fc", "-f", output_file]

        if schema_only:
            cmd.append("--schema-only")

        if tables:
            for table in tables:
                cmd.extend(["-t", table])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise AdapterError(f"pg_dump failed:\n{result.stderr}")

    def restore(self, url: str, config: RestoreConfig):
        format_type = self._detect_restore_format(config.input_file)

        if format_type == "sql":
            cmd = ["psql", url, "-f", config.input_file]
            error_prefix = "psql"
        else:
            cmd = ["pg_restore", "-d", url]

            if config.clean:
                cmd.append("--clean")

            if config.jobs is not None:
                cmd.extend(["-j", str(config.jobs)])

            cmd.append(config.input_file)
            error_prefix = "pg_restore"

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise AdapterError(f"{error_prefix} failed:\n{result.stderr}")

    def _detect_restore_format(self, input_file: str) -> str:
        if Path(input_file).suffix.lower() == ".sql":
            return "sql"

        return "archive"

    def test_connection(self, url: str) -> bool:
        result = subprocess.run(
            ["psql", url, "-c", "\\q"],
            capture_output=True,
            text=True,
        )

        return result.returncode == 0
