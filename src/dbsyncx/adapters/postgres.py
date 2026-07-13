import subprocess
from typing import Optional, List

from .base import DatabaseAdapter
from ..exceptions import AdapterError


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

    def restore(
        self,
        url: str,
        input_file: str,
        schema_only: bool = False,
        tables: Optional[List[str]] = None,
    ):
        cmd = ["pg_restore", "-d", url, "--clean", "--if-exists", input_file]

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
            raise AdapterError(f"pg_restore failed:\n{result.stderr}")

    def test_connection(self, url: str) -> bool:
        result = subprocess.run(
            ["psql", url, "-c", "\\q"],
            capture_output=True,
            text=True,
        )

        return result.returncode == 0
