FROM python:3.11-slim-bookworm

WORKDIR /bot

RUN apt-get update && apt-get install git netcat-openbsd iproute2 debuginfod python3.11-dbg -yqq && rm -rf /var/lib/apt/lists/*

# ENV DEBUGINFOD_URLS="https://debuginfod.elfutils.org/"
# ENV POETRY_VIRTUALENVS_CREATE="false"
# ENV PYTHONPATH="/usr/local/lib/python311.zip:/usr/local/lib/python3.11:/usr/local/lib/python3.11/lib-dynload:/usr/local/lib/python3.11/site-packages"
RUN pip install poetry

COPY vibr/pyproject.toml vibr/poetry.lock ./

RUN poetry install --no-root --only main

COPY . .
RUN mkdir wow

CMD ["sh", "vibr/entrypoint.sh"]
