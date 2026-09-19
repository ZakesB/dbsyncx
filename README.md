<p align="center">
  <h1 align="center">dbsyncx</h1>
  <p align="center">
    Sync and backup databases like Git.
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.4.0-blue.svg" />
  <img src="https://img.shields.io/badge/python-3.9%2B-blue.svg" />
  <img src="https://img.shields.io/badge/license-MIT-green.svg" />
  <img src="https://img.shields.io/badge/status-active-blue.svg" />
</p>

---

## What is dbsyncx?

**dbsyncx** is a developer-first CLI that makes it easy to:

* Sync databases between environments
* Create backups instantly
* Avoid complex `pg_dump` commands
* Work safely with production data

Think of it as:

> **Git-style workflow for your database**

---

## Why dbsyncx?

If you've ever:

* Needed to debug production locally
* Run risky migrations without a backup
* Forgotten `pg_dump` flags
* Accidentally overwritten the wrong DB 😅

Then dbsyncx is for you.

---

## Features

* Sync databases (pull / push)
* One-command database backups
* Restore from backup dumps
* Schema-only syncs and backups
* Table-specific syncs and backups
* Built-in safety confirmations
* Dry-run mode (preview actions)
* Clean YAML configuration
* Adapter-based architecture
* Fully local (no cloud required)
* Optional Google Drive backup storage

---

## Example

### Pull production → local

```bash
dbsyncx pull production local
```

```text
This will overwrite 'local'. Continue? [y/N]:
12:41:03 | INFO | Pulling database: production -> local
12:41:05 | INFO | Dumping source database
12:41:07 | INFO | Restoring into target database
✔ Pull complete
```

---

### Create a backup

```bash
dbsyncx dump production
```

```text
✔ Dump created: dbsyncx_production_20260427_125102.dump
```

---

## Installation

### Requirements

Make sure PostgreSQL tools are installed:

```bash
pg_dump --version
pg_restore --version
psql --version
```

---

### Install

```bash
pip install dbsyncx
```

Or from source:

```bash
pip install -e .
```

---

### Verify

```bash
dbsyncx version
```
```text
dbsyncx is at version 1.4.0
```

---

## Quick Start

### 1. Initialize

```bash
dbsyncx init
```

---

### 2. Configure

Edit:

```
.dbsyncx/config.yaml
```

```yaml
project_id: my-project

databases:
  local:
    url: postgresql://localhost:5432/mydb

  production:
    url: postgresql://user:password@host:5432/mydb
```

---

### 3. Test connection

```bash
dbsyncx status local
```

---

### 4. Sync database

```bash
dbsyncx pull production local
```

---

## Commands

### Initialize config

```bash
dbsyncx init
```

---

### Pull database

```bash
dbsyncx pull <source> <target>
```

Options:

```bash
--force, -f       Skip confirmation
--dry-run         Simulate without executing
--schema-only     Sync schema objects only
--table, -t       Limit sync to a table. Repeat for multiple tables
```

Examples:

```bash
dbsyncx pull production local --schema-only
dbsyncx pull production local --table public.users --table audit_log
```

---

### Push database

```bash
dbsyncx push <source> <target>
```

Options:

```bash
--force, -f       Skip confirmation
--dry-run         Simulate without executing
--schema-only     Sync schema objects only
--table, -t       Limit sync to a table. Repeat for multiple tables
```

Examples:

```bash
dbsyncx push local staging --schema-only
dbsyncx push local staging --table public.users
```

---

### Dump database (backup)

```bash
dbsyncx dump <database>
```

Options:

```bash
--output, -o      Custom output file
--dry-run         Simulate without executing
--schema-only     Dump schema objects only
--table, -t       Limit dump to a table. Repeat for multiple tables
```

Examples:

```bash
dbsyncx dump production --schema-only
dbsyncx dump production --table public.users --output users.dump
```

### Back up to Google Drive

Install the optional Google Drive dependencies:

```bash
pip install "dbsyncx[gdrive]"
```

In Google Cloud, enable the Drive API and create either a Desktop OAuth client
JSON file or a service-account JSON key. For a service account, share the
target Drive folder with the service-account email. Then configure the backup
provider:

```yaml
backup:
  provider: gdrive
  directory: backups              # local backup catalog location
  catalog: catalog.json
  credentials_file: ${GOOGLE_APPLICATION_CREDENTIALS}
  token_file: .dbsyncx/gdrive-token.json   # OAuth only; optional
  folder_id: 1a2b3cYourDriveFolderId        # optional; recommended
  # folder_name: dbsyncx-backups            # used when folder_id is omitted
  # shared_drive_id: 0AExampleSharedDriveId # optional; enables Shared Drive support
```

The first OAuth backup opens a browser for Google consent and stores the
refresh token at `token_file`. Each `dbsyncx dump <database>` still creates a
local dump, then uploads it to Drive. The local catalog records the Drive file
ID, so `dbsyncx backup list`, `info`, and `delete` manage the uploaded backup.

To use a Shared Drive, set `shared_drive_id` and, preferably, the ID of its
target folder in `folder_id`. When `folder_id` is omitted, dbsyncx finds or
creates `folder_name` in the Shared Drive root. The account behind the OAuth
credentials or service-account key must be a member of that Shared Drive with
permission to create and delete files.

### Retain backups automatically

Set a retention policy to remove old backups after each successful dump:

```yaml
backup:
  retention:
    enabled: true
    keep_last: 7       # always retain the seven newest backups per database
    max_age_days: 30   # prune older backups after the keep-last protection
```

Policies apply separately to each database and only to backups owned by the
currently configured storage provider. With both limits set, dbsyncx keeps the
newest `keep_last` backups even if they are older than `max_age_days`; an older
backup is removed only when it exceeds the age limit. To inspect the result
without deleting anything, run:

```bash
dbsyncx backup prune --dry-run
```

`dbsyncx backup prune` lists the selected backups and asks for confirmation;
use `--force` only for unattended jobs.

---

### Restore database

```bash
dbsyncx restore <database> <dump-file>
```

Options:

```bash
--force, -f       Skip confirmation
--dry-run         Simulate without executing
--schema-only     Restore schema objects only
--table, -t       Limit restore to a table. Repeat for multiple tables
```

Examples:

```bash
dbsyncx restore local production.dump
dbsyncx restore local users.dump --table public.users
```

Restore uses `pg_restore --clean --if-exists`, so matching target objects can be dropped and recreated during restore without failing on empty targets.

---

### Check connection

```bash
dbsyncx status <database>
```

---

### Version

```bash
dbsyncx version
```

---

## Safety Features

dbsyncx protects you by default:

* Prompts before overwriting databases
* `--force` to skip confirmation
* `--dry-run` to simulate actions

---

## Security

* Runs entirely locally
* No credentials leave your machine
* No cloud dependency
* Uses native PostgreSQL tools

---

## How it works

dbsyncx uses:

* `pg_dump` → export database
* `pg_restore` → restore database

No magic — just safer workflows.

---

## Architecture

Adapter-based design:

Current:

* ✅ PostgreSQL

Future:

* MySQL
* SQLite
* MongoDB

---

## Roadmap

### v1.0.0

* CLI sync tool
* Backup support
* Safety features

### v1.1.0

* Added support for running `dbsyncx` in local, Docker, and crontab environments.
* Refactored configuration loading to work seamlessly across all supported execution environments.

### v1.4.0 (Current)

* Schema-only sync
* Table-specific sync
* Restore from dump files
* Google Drive backup storage
* Google Shared Drive backup storage
* Configurable backup retention policies

### v1.3.0

* Cloud dashboard
* Sync history

### v2.0.0

* Multi-database support

---

## Development

```bash
git clone https://github.com/yourusername/dbsyncx
cd dbsyncx

pip install -e .[dev]
pytest
```

---

## Contributing

Contributions welcome.

Open issues or PRs.

---

## License

MIT

---

## Support

If you find this useful:

* ⭐ Star the repo
* Share with your team
* Suggest features

---

## Coming Soon

Optional cloud dashboard for:

* Sync monitoring
* Scheduled backups
* Team workflows

CLI will always remain free.

---

<p align="center">
  Built for developers who are tired of database headaches.
</p>
