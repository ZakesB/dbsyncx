"""Selection logic for backup retention policies."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional

from dbsyncx.backup.models import Backup, RetentionPolicy
from dbsyncx.exceptions import ConfigError


def retention_policy_from_config(config: Optional[Dict[str, object]]) -> RetentionPolicy:
    """Build and validate a retention policy from the ``backup`` config section."""
    if config is None:
        config = {}
    if not isinstance(config, dict):
        raise ConfigError("backup.retention must be a mapping")
    keep_last = config.get("keep_last")
    max_age_days = config.get("max_age_days")

    for name, value in (("keep_last", keep_last), ("max_age_days", max_age_days)):
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
            raise ConfigError(f"backup.retention.{name} must be a non-negative integer")

    enabled = config.get("enabled", False)
    if not isinstance(enabled, bool):
        raise ConfigError("backup.retention.enabled must be true or false")

    return RetentionPolicy(
        enabled=enabled,
        keep_last=keep_last,
        max_age_days=max_age_days,
    )


def backups_to_prune(
    backups: Iterable[Backup],
    policy: RetentionPolicy,
    now: Optional[datetime] = None,
) -> List[Backup]:
    """Return backups that violate every configured retention limit.

    Backups are grouped by database so retaining the latest backups for one
    database never removes the only backup for another. When both limits are
    configured, the newest ``keep_last`` backups are always protected and older
    backups are removed only after exceeding ``max_age_days``.
    """
    if policy.keep_last is None and policy.max_age_days is None:
        return []

    now = now or datetime.now()
    grouped: Dict[str, List[Backup]] = defaultdict(list)
    for backup in backups:
        grouped[backup.metadata.database].append(backup)

    selected: List[Backup] = []
    for database_backups in grouped.values():
        ordered = sorted(
            database_backups,
            key=lambda backup: backup.metadata.created_at,
            reverse=True,
        )
        protected_ids = {
            backup.metadata.id for backup in ordered[: policy.keep_last]
        } if policy.keep_last is not None else set()

        for backup in ordered:
            outside_keep_last = backup.metadata.id not in protected_ids
            exceeds_age = (
                policy.max_age_days is not None
                and backup.metadata.created_at < now - timedelta(days=policy.max_age_days)
            )

            if policy.keep_last is None:
                should_prune = exceeds_age
            elif policy.max_age_days is None:
                should_prune = outside_keep_last
            else:
                should_prune = outside_keep_last and exceeds_age

            if should_prune:
                selected.append(backup)

    return selected
