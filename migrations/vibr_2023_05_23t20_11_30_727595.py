from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.table import Table

ID = "2023-05-23T20:11:30:727595"
VERSION = "0.111.1"
DESCRIPTION = "Add composite unique to PlaylistToSong"


async def forwards() -> MigrationManager:
    manager = MigrationManager(migration_id=ID, app_name="", description=DESCRIPTION)

    async def composite_unique() -> None:
        class RawTable(Table):
            ...

        await RawTable.raw("ALTER TABLE playlist_to_song ADD UNIQUE (playlist, song);")
        await RawTable.raw("ALTER TABLE song ADD UNIQUE (lavalink_id);")

    manager.add_raw(composite_unique)

    return manager
