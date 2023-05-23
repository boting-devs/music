from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import BigInt, SmallInt
from piccolo.columns.indexes import IndexMethod

ID = "2023-05-23T17:52:37:451219"
VERSION = "0.111.1"
DESCRIPTION = "Add player config persistence"


async def forwards() -> MigrationManager:
    manager = MigrationManager(
        migration_id=ID, app_name="vibr", description=DESCRIPTION
    )

    manager.add_table("PlayerConfig", tablename="player_config")

    manager.add_column(
        table_class_name="PlayerConfig",
        tablename="player_config",
        column_name="channel_id",
        db_column_name="channel_id",
        column_class_name="BigInt",
        column_class=BigInt,
        params={
            "default": 0,
            "null": False,
            "primary_key": True,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
    )

    manager.add_column(
        table_class_name="PlayerConfig",
        tablename="player_config",
        column_name="volume",
        db_column_name="volume",
        column_class_name="SmallInt",
        column_class=SmallInt,
        params={
            "default": 0,
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
    )

    return manager
