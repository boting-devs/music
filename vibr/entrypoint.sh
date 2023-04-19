until nc -w 10 postgres 5432; do sleep 1; done
poetry run alembic upgrade head
poetry run task start
