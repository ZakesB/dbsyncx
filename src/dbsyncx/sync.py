import tempfile
from pathlib import Path

from .config import get_database_url
from .adapters import get_adapter
from .exceptions import DbSyncXError
from .logging import logger
from .utils import success
from datetime import datetime


def pull_db(config, source: str, target: str, dry_run: bool = False):

    source_url = get_database_url(config, source)
    target_url = get_database_url(config, target)

    adapter = get_adapter(source_url)

    logger.info(f"Pulling database: {source} -> {target}")

    if dry_run:
        logger.info("[DRY RUN] Would dump source database")
        logger.info("[DRY RUN] Would restore into target database")
        success("Dry run complete")
        return

    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            dump_file = tmp.name

        logger.info("Dumping source database...")
        adapter.dump(source_url, dump_file)

        logger.info("Restoring into target database...")
        adapter.restore(target_url, dump_file)

        success("Pull complete")

    except Exception as e:
        raise DbSyncXError(f"Sync failed: {str(e)}")

    finally:
        if "dump_file" in locals():
            Path(dump_file).unlink(missing_ok=True)


def push_db(config, source: str, target: str):
    """
    Push database from source -> target
    """

    source_url = get_database_url(config, source)
    target_url = get_database_url(config, target)

    adapter = get_adapter(source_url)

    logger.info(f"Pushing database: {source} -> {target}")

    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            dump_file = tmp.name

        logger.info("Dumping source database...")
        adapter.dump(source_url, dump_file)

        logger.info("Restoring into target database...")
        adapter.restore(target_url, dump_file)

        success("Push complete")

    except Exception as e:
        raise DbSyncXError(f"Sync failed: {str(e)}")

    finally:
        if "dump_file" in locals():
            try:
                Path(dump_file).unlink(missing_ok=True)
            except Exception:
                pass

def dump_db(config, name: str, output: str = None, dry_run: bool = False):
    url = get_database_url(config, name)
    adapter = get_adapter(url)

    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"dbsyncx_{name}_{timestamp}.dump"

    logger.info(f"Dumping database: {name}")

    if dry_run:
        logger.info(f"[DRY RUN] Would dump to file: {output}")
        success("Dry run complete")
        return

    try:
        adapter.dump(url, output)
        success(f"Dump created: {output}")

    except Exception as e:
        raise DbSyncXError(f"Dump failed: {str(e)}")