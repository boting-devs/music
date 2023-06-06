from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import Timestamptz
from piccolo.columns.indexes import IndexMethod

ID = "2023-05-30T20:01:05:555391"
VERSION = "0.111.1"
DESCRIPTION = "Add User.topgg_voted"


async def forwards() -> MigrationManager:
    manager = MigrationManager(
        migration_id=ID, app_name="vibr", description=DESCRIPTION
    )

    manager.add_column(
        table_class_name="User",
        tablename="users",
        column_name="topgg_voted",
        db_column_name="topgg_voted",
        column_class_name="Timestamptz",
        column_class=Timestamptz,
        params={
            "default": None,
            "null": True,
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
