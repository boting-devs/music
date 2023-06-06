from logging import Formatter, LogRecord, StreamHandler, getLogger


class DispatchingFormatter(Formatter):
    def __init__(
        self, formatters: dict[str, Formatter], default_formatter: Formatter
    ) -> None:
        self._formatters = formatters
        self._default_formatter = default_formatter

    def format(self, record: LogRecord) -> str:
        formatter = self._formatters.get(
            record.name.split(".")[0], self._default_formatter
        )
        return formatter.format(record)


def setup_logging() -> None:
    root = getLogger()
    handler = StreamHandler()
    mafic_formatter = Formatter(
        "%(levelname)-7s %(asctime)s [%(label)-10s] (guild: %(guild)-19d): %(message)s",
        datefmt="%H:%M:%S %d/%m/%Y",
        defaults={"guild": 0, "label": "None"},
    )
    vibr_formatter = Formatter(
        "%(levelname)-7s %(asctime)s              (guild: %(guild)-19d): %(message)s",
        datefmt="%H:%M:%S %d/%m/%Y",
        defaults={"guild": 0},
    )
    default_formatter = Formatter(
        "%(levelname)-7s %(asctime)s %(filename)12s:%(funcName)-28s: %(message)s",
        datefmt="%H:%M:%S %d/%m/%Y",
    )
    formatter = DispatchingFormatter(
        {"mafic": mafic_formatter, "vibr": vibr_formatter}, default_formatter
    )
    handler.setFormatter(formatter)
    root.handlers = []
    root.addHandler(handler)
