FROM --platform=amd64 python:3.10-slim-buster

WORKDIR /bot

RUN apt update && apt install build-essential git -y && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root --no-dev

COPY . .

ENTRYPOINT ["poetry", "run", "python3"]
CMD ["-m", "vibr"]
