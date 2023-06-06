from piccolo.conf.apps import AppConfig, table_finder

APP_CONFIG = AppConfig(
    app_name="vibr",
    migrations_folder_path="migrations",
    table_classes=table_finder(["vibr.db"], exclude_imported=False),
    migration_dependencies=["botbase.piccolo_app"],
    commands=[],
)
