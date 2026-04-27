from dbsyncx.adapters.postgres import PostgresAdapter


def test_postgres_adapter_exists():
    adapter = PostgresAdapter()
    assert adapter is not None