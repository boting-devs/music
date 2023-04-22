FROM python:3.11-slim-bullseye

WORKDIR /manager

RUN pip install poetry

COPY manager/pyproject.toml manager/poetry.lock ./

RUN poetry install --no-root --only main

COPY . .

ENTRYPOINT ["poetry", "run", "python3"]
CMD ["-m", "manager"]
