from asyncio import sleep
from os import environ as env
from os import getenv
from typing import Any

from nextcord.ext.ipc import Client
from quart import Quart, Response, abort, request


def create_client():
    return Client(secret_key="pain.", host=env["IPC_SERVER"], port=int(env["IPC_PORT"]))


client = create_client()
app = Quart(__name__)


async def ipc(route: str, **kwargs: Any):
    global client
    for _ in range(5):
        try:
            return await client.request(route, **kwargs)
        except (ConnectionResetError, AttributeError):
            await sleep(1)
            client = create_client()

    abort(503)


@app.route("/vibr/vote", methods=["POST"])
async def vote():
    data = await request.get_json()
    try:
        auth = request.headers["Authorization"]
    except KeyError:
        return Response(status=401)

    if auth == getenv("TOPGG_AUTH"):
        response = await ipc("topgg", data_type=data["type"], user=data["user"])

        if "error" in response:
            print(response["error"])
            print(response)
            return Response(status=500)
        else:
            if data["type"] == "test":
                print("Recieved test")
            else:
                print(f"{data['user']} voted.")

            return Response(status=204)

    return Response(status=403)
