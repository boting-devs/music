FROM --platform=amd64 python:3.9-slim-buster
ARG user

USER $user

WORKDIR /bot

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root --no-dev

COPY . .

ENTRYPOINT ["poetry", "run", "python3"]
CMD ["-m", "vibr"]
