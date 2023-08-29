FROM alpine

WORKDIR /bot

RUN apk add --no-cache --update git netcat-openbsd iproute2 python3 python3-dbg py3-pip python3-dev gcc
# ENV DEBUGINFOD_URLS="https://debuginfod.elfutils.org/"
RUN python3 -m pip install poetry --break-system-packages

# COPY vibr/pyproject.toml vibr/poetry.lock ./
COPY vibr/requirements.txt ./

RUN pip install -r requirements.txt

COPY . .
RUN mkdir wow

CMD ["sh", "vibr/entrypoint.sh"]
