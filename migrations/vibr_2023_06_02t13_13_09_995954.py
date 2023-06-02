from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import Text
from piccolo.columns.column_types import Varchar
from piccolo.columns.indexes import IndexMethod


ID = "2023-06-02T13:13:09:995954"
VERSION = "0.111.1"
DESCRIPTION = "Store node session ids"


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="vibr", description=DESCRIPTION
    )

    manager.add_table("Node", tablename="node")

    manager.add_column(
        table_class_name="Node",
        tablename="node",
        column_name="label",
        db_column_name="label",
        column_class_name="Text",
        column_class=Text,
        params={
            "default": "",
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
        table_class_name="Node",
        tablename="node",
        column_name="session_id",
        db_column_name="session_id",
        column_class_name="Varchar",
        column_class=Varchar,
        params={
            "length": 16,
            "default": "",
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
