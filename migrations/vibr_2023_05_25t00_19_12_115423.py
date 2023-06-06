from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.table import Table

ID = "2023-05-25T00:19:12:115423"
VERSION = "0.111.1"
DESCRIPTION = "Add composite unique to SongLog"


async def forwards() -> MigrationManager:
    manager = MigrationManager(migration_id=ID, app_name="", description=DESCRIPTION)

    async def composite_unique() -> None:
        class RawTable(Table):
            ...

        await RawTable.raw(
            "ALTER TABLE song_log ADD UNIQUE (type, identifier, user_id);"
        )

    manager.add_raw(composite_unique)

    return manager
