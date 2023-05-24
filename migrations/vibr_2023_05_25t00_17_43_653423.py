from enum import Enum

from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import BigInt, Integer, Serial, SmallInt, Text
from piccolo.columns.indexes import IndexMethod

ID = "2023-05-25T00:17:43:653423"
VERSION = "0.111.1"
DESCRIPTION = "Add song logging"


async def forwards() -> MigrationManager:
    manager = MigrationManager(
        migration_id=ID, app_name="vibr", description=DESCRIPTION
    )

    manager.add_table("SongLog", tablename="song_log")

    manager.add_column(
        table_class_name="SongLog",
        tablename="song_log",
        column_name="id",
        db_column_name="id",
        column_class_name="Serial",
        column_class=Serial,
        params={
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
        table_class_name="SongLog",
        tablename="song_log",
        column_name="type",
        db_column_name="type",
        column_class_name="SmallInt",
        column_class=SmallInt,
        params={
            "default": 10,
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": Enum(
                "Type",
                {
                    "BANDCAMP": 0,
                    "DISCORD": 1,
                    "SOUNDCLOUD": 2,
                    "TWITCH": 3,
                    "VIMEO": 4,
                    "YOUTUBE": 5,
                    "APPLE_MUSIC": 6,
                    "DEEZER": 7,
                    "SPOTIFY": 8,
                    "OTHER": 9,
                },
            ),
            "db_column_name": None,
            "secret": False,
        },
    )

    manager.add_column(
        table_class_name="SongLog",
        tablename="song_log",
        column_name="identifier",
        db_column_name="identifier",
        column_class_name="Text",
        column_class=Text,
        params={
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

    manager.add_column(
        table_class_name="SongLog",
        tablename="song_log",
        column_name="user_id",
        db_column_name="user_id",
        column_class_name="BigInt",
        column_class=BigInt,
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

    manager.add_column(
        table_class_name="SongLog",
        tablename="song_log",
        column_name="amount",
        db_column_name="amount",
        column_class_name="Integer",
        column_class=Integer,
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
