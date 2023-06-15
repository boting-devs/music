from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import Text

ID = "2023-06-14T22:02:56:606323"
VERSION = "0.111.1"
DESCRIPTION = "spotify id none"


async def forwards() -> MigrationManager:
    manager = MigrationManager(
        migration_id=ID, app_name="vibr", description=DESCRIPTION
    )

    manager.alter_column(
        table_class_name="User",
        tablename="users",
        column_name="spotify_id",
        db_column_name="spotify_id",
        params={"default": None},
        old_params={"default": ""},
        column_class=Text,
        old_column_class=Text,
    )

    return manager
