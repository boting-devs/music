from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.table import Table

ID = "2023-06-07T01:34:42:391410"
VERSION = "0.111.1"
DESCRIPTION = ""


async def forwards() -> MigrationManager:
    manager = MigrationManager(migration_id=ID, app_name="", description=DESCRIPTION)

    async def composite_unique() -> None:
        class RawTable(Table):
            ...

        await RawTable.raw("ALTER TABLE node ADD UNIQUE (label, session_id);")

    manager.add_raw(composite_unique)

    return manager
