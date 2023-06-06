FROM python:3.11-slim-bullseye

WORKDIR /bot

RUN apt-get update && apt-get install netcat-openbsd -yqq && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

COPY api/pyproject.toml api/poetry.lock ./

RUN poetry install --no-root --only main

COPY . .

CMD ["sh", "api/entrypoint.sh"]
