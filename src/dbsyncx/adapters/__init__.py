from .postgres import PostgresAdapter
from ..exceptions import AdapterError


def get_adapter(url: str):
    """
    Return correct adapter based on DB URL.
    """

    if url.startswith("postgresql://") or url.startswith("postgres://"):
        return PostgresAdapter()

    raise AdapterError(f"Unsupported database type for URL: {url}")