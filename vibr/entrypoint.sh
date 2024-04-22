until nc -w 1 postgres 5432; do sleep 0.1; done
export HOST_IP=$(ip route show | awk '/default/ {print $3}')
poetry run piccolo migrations forwards all
until (
    nc -w 1 $HOST_IP 6783 \
    || nc -w 1 $HOST_IP 5783 \
    || nc -w 1 lavalink 6969 2>&1 >> /dev/null
); do sleep 0.1; done
poetry run task start
