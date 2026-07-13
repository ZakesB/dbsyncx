from dbsyncx.adapters.postgres import PostgresAdapter


def test_postgres_adapter_exists():
    adapter = PostgresAdapter()
    assert adapter is not None


def test_dump_supports_schema_only_and_tables(monkeypatch):
    calls = []

    def fake_run(cmd, capture_output, text):
        calls.append(cmd)

        class Result:
            returncode = 0
            stderr = ""

        return Result()

    monkeypatch.setattr("subprocess.run", fake_run)

    adapter = PostgresAdapter()
    adapter.dump(
        "postgresql://localhost/source",
        "backup.dump",
        schema_only=True,
        tables=["public.users", "audit_log"],
    )

    assert calls == [
        [
            "pg_dump",
            "postgresql://localhost/source",
            "-Fc",
            "-f",
            "backup.dump",
            "--schema-only",
            "-t",
            "public.users",
            "-t",
            "audit_log",
        ]
    ]


def test_restore_supports_schema_only_and_tables(monkeypatch):
    calls = []

    def fake_run(cmd, capture_output, text):
        calls.append(cmd)

        class Result:
            returncode = 0
            stderr = ""

        return Result()

    monkeypatch.setattr("subprocess.run", fake_run)

    adapter = PostgresAdapter()
    adapter.restore(
        "postgresql://localhost/target",
        "backup.dump",
        schema_only=True,
        tables=["public.users", "audit_log"],
    )

    assert calls == [
        [
            "pg_restore",
            "-d",
            "postgresql://localhost/target",
            "--clean",
            "--if-exists",
            "backup.dump",
            "--schema-only",
            "-t",
            "public.users",
            "-t",
            "audit_log",
        ]
    ]
