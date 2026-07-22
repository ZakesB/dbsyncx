import os
import tempfile
from pathlib import Path
from typing import Optional, List
import uuid

from dbsyncx.backup import create_backup_manager
from dbsyncx.backup.models import Backup, BaseMetadataModel
from dbsyncx import __version__

from .config import get_database_url
from .adapters import get_adapter
from .exceptions import DbSyncXError
from .logging import logger
from .utils import success
from datetime import datetime


def _scope_description(schema_only: bool = False, tables: Optional[List[str]] = None) -> str:
    scope = []

    if schema_only:
        scope.append("schema only")

    if tables:
        scope.append(f"tables: {', '.join(tables)}")

    return "; ".join(scope) if scope else "full database"


def pull_db(
    config,
    source: str,
    target: str,
    dry_run: bool = False,
    schema_only: bool = False,
    tables: Optional[List[str]] = None,
):

    source_url = get_database_url(config, source)
    target_url = get_database_url(config, target)

    adapter = get_adapter(source_url)

    logger.info(f"Pulling database: {source} -> {target} ({_scope_description(schema_only, tables)})")

    if dry_run:
        logger.info(f"[DRY RUN] Would dump source database ({_scope_description(schema_only, tables)})")
        logger.info(f"[DRY RUN] Would restore into target database ({_scope_description(schema_only, tables)})")
        success("Dry run complete")
        return

    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            dump_file = tmp.name

        logger.info("Dumping source database...")
        adapter.dump(source_url, dump_file, schema_only=schema_only, tables=tables)

        logger.info("Restoring into target database...")
        adapter.restore(target_url, dump_file, schema_only=schema_only, tables=tables)

        success("Pull complete")

    except Exception as e:
        raise DbSyncXError(f"Sync failed: {str(e)}")

    finally:
        if "dump_file" in locals():
            Path(dump_file).unlink(missing_ok=True)


def push_db(
    config,
    source: str,
    target: str,
    dry_run: bool = False,
    schema_only: bool = False,
    tables: Optional[List[str]] = None,
):
    """
    Push database from source -> target
    """

    source_url = get_database_url(config, source)
    target_url = get_database_url(config, target)

    adapter = get_adapter(source_url)

    logger.info(f"Pushing database: {source} -> {target} ({_scope_description(schema_only, tables)})")

    if dry_run:
        logger.info(f"[DRY RUN] Would dump source database ({_scope_description(schema_only, tables)})")
        logger.info(f"[DRY RUN] Would restore into target database ({_scope_description(schema_only, tables)})")
        success("Dry run complete")
        return

    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            dump_file = tmp.name

        logger.info("Dumping source database...")
        adapter.dump(source_url, dump_file, schema_only=schema_only, tables=tables)

        logger.info("Restoring into target database...")
        adapter.restore(target_url, dump_file, schema_only=schema_only, tables=tables)

        success("Push complete")

    except Exception as e:
        raise DbSyncXError(f"Sync failed: {str(e)}")

    finally:
        if "dump_file" in locals():
            try:
                Path(dump_file).unlink(missing_ok=True)
            except Exception:
                pass

def dump_db(
    config,
    name: str,
    output: str = None,
    dry_run: bool = False,
    schema_only: bool = False,
    tables: Optional[List[str]] = None,
):
    url = get_database_url(config, name)
    adapter = get_adapter(url)

    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"dbsyncx_{name}_{timestamp}.dump"

    logger.info(f"Dumping database: {name} ({_scope_description(schema_only, tables)})")

    if dry_run:
        logger.info(f"[DRY RUN] Would dump to file: {output} ({_scope_description(schema_only, tables)})")
        success("Dry run complete")
        return

    try:
        adapter.dump(url, output, schema_only=schema_only, tables=tables)
        manager = create_backup_manager(config)
        backup = Backup(
            metadata=BaseMetadataModel(
                id=str(uuid.uuid4()),
                database=name,
                created_at=datetime.now(),
                size=os.stat(output).st_size,
                checksum=None,          # TODO: Compute SHA256
                duration=None,          # TODO: Capture dump duration
                db_version=None,        # TODO: Populate from adapter
                tool_version=__version__,
            ),
            filename=output,
            provider=config["backup"]["provider"],
            location=str(Path(output).parent.resolve()),
            path=str(output),
        )

        manager.register_backup(backup=backup)
        success(f"Dump created: {output}")

    except Exception as e:
        raise DbSyncXError(f"Dump failed: {str(e)}")


def restore_db(
    config,
    name: str,
    input_file: str,
    dry_run: bool = False,
    schema_only: bool = False,
    tables: Optional[List[str]] = None,
):
    url = get_database_url(config, name)
    adapter = get_adapter(url)

    logger.info(f"Restoring database: {name} <- {input_file} ({_scope_description(schema_only, tables)})")

    if dry_run:
        logger.info(f"[DRY RUN] Would restore from file: {input_file} ({_scope_description(schema_only, tables)})")
        success("Dry run complete")
        return

    try:
        adapter.restore(url, input_file, schema_only=schema_only, tables=tables)
        success(f"Restore complete: {name}")

    except Exception as e:
        raise DbSyncXError(f"Restore failed: {str(e)}")
