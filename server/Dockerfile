
FROM --platform=amd64 python:3.10-slim-buster

WORKDIR /server

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root --no-dev

COPY . .

ENTRYPOINT ["poetry", "run", "hypercorn", "--config", "file:config.py", "server:app"]
