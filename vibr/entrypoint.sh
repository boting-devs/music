until nc -w 10 postgres 5432; do sleep 1; done
export HOST_IP=$(ip route show | awk '/default/ {print $3}')
ip route show
poetry run alembic upgrade head
poetry run task start
