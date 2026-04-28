from abc import ABC, abstractmethod
from typing import Optional, List


class DatabaseAdapter(ABC):
    """
    Base adapter interface for all database types.
    """

    @abstractmethod
    def dump(
        self,
        url: str,
        output_file: str,
        schema_only: bool = False,
        tables: Optional[List[str]] = None,
    ):
        """
        Export database to file.
        """
        pass

    @abstractmethod
    def restore(
        self,
        url: str,
        restore_config,
    ):
        """
        Restore database from config.
        """
        pass

    @abstractmethod
    def test_connection(self, url: str) -> bool:
        """
        Test if database is reachable.
        """
        pass