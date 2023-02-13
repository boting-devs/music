FROM python:3.10-slim-buster

WORKDIR /bot

RUN apt-get update && apt-get install git netcat-openbsd -yqq && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root --only main

COPY . .

CMD ["sh", "entrypoint.sh"]
