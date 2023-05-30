until nc -w 1 postgres 5432; do sleep 0.1; done
export HOST_IP=$(ip route show | awk '/default/ {print $3}')
poetry run piccolo migrations forwards all
sleep 1
poetry run task start