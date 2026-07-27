from typing import Dict, Type

from dbsyncx.storage.base import StorageProvider
from dbsyncx.storage.local import LocalStorageProvider



class StorageRegistry:
    """
    Registry for managing storage providers.
    """

    _providers: Dict[str, Type[StorageProvider]] = {}

    @classmethod
    def register_provider(cls, provider_class: Type[StorageProvider]) -> None:
        """
        Registers a storage provider class.

        Args
            provider_class: The storage provider class to register.
        """
        if not issubclass(provider_class, StorageProvider):
            raise ValueError(f"{provider_class} is not a subclass of StorageProvider")
        cls._providers[provider_class.name] = provider_class

    @classmethod
    def get_provider(cls, name: str) -> Type[StorageProvider]:
        """
        Retrieves a registered storage provider class by name.

        Args
            name: The name of the storage provider.
        Returns
            The storage provider class.
        """
        provider_class = cls._providers.get(name)
        if provider_class is None:
            raise ValueError(f"Storage provider '{name}' is not registered.")
        return provider_class

    @classmethod
    def list_providers(cls) -> Dict[str, Type[StorageProvider]]:
        """
        Lists all registered storage providers.

        Returns
            A dictionary of registered storage providers.
        """
        return sorted(cls._providers.items(), key=lambda x: x[0])

# Register all providers that you will use here
StorageRegistry.register_provider(LocalStorageProvider)