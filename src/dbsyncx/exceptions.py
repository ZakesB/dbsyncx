class DbSyncXError(Exception):
    pass


class ConfigError(DbSyncXError):
    pass


class AdapterError(DbSyncXError):
    pass


class ConnectionError(DbSyncXError):
    pass