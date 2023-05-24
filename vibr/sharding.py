from os import environ

import docker
import requests

docker = docker.APIClient(base_url="unix:///var/run/docker.sock")
HOSTNAME = environ["HOSTNAME"]
all_containers = docker.containers()
our_container = [c for c in all_containers if c["Id"][:12] == HOSTNAME[:12]][0]
CURRENT_CLUSTER = our_container["Labels"]["com.docker.compose.container-number"]
# Find which number we are in the list of "replicas".
# This abuses replicas like it is just deploying them as different clusters.

TOTAL_CLUSTERS = int(environ["TOTAL_CLUSTERS"])
# Request proxy's current shard count, as the single 'source of truth'.
TOTAL_SHARDS = int(requests.get(f"{environ['PROXY_HTTP']}/shard_count", timeout=5).text)
SHARD_COUNT = TOTAL_SHARDS // TOTAL_CLUSTERS
shard_ids = list(
    range(
        SHARD_COUNT * (int(CURRENT_CLUSTER) - 1),
        SHARD_COUNT * (int(CURRENT_CLUSTER)),
    )
)

if CURRENT_CLUSTER == TOTAL_CLUSTERS:
    shard_ids.extend(
        range(
            SHARD_COUNT * TOTAL_CLUSTERS,
            TOTAL_SHARDS,
        )
    )
