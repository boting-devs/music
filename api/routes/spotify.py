from datetime import UTC, datetime
from os import environ
from secrets import token_urlsafe

from async_spotify import SpotifyApiClient
from async_spotify.authentification.authorization_flows import AuthorizationCodeFlow
from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRouter
from itsdangerous import BadSignature, URLSafeSerializer
from ormar import NoMatch

from vibr.db import User

FIVE_MINUTES = 1000 * 60 * 5
SERIALIZER = URLSafeSerializer(secret_key=environ["OAUTH_SECRET_KEY"], salt="vibr")
REDIRECT_URI = f"{environ['REDIRECT_URI']}/spotify/callback"

router = APIRouter(prefix="/spotify")
auth_flow = AuthorizationCodeFlow(
    application_id=environ["SPOTIFY_CLIENT_ID"],
    application_secret=environ["SPOTIFY_CLIENT_SECRET"],
    scopes=["playlist-read-private"],
    redirect_url=REDIRECT_URI,
)

api_client = SpotifyApiClient(auth_flow)


async def init() -> None:
    await api_client.create_new_client(request_limit=1500)
    __import__("logging").critical(SERIALIZER.dumps(305017820775710720))


@router.get("/authorize")
async def authorize(request: Request):
    signed_user_id = request.query_params["user"]
    user_id: int = SERIALIZER.loads(signed_user_id)

    random_state = token_urlsafe(nbytes=12)
    state = SERIALIZER.dumps((random_state, user_id))
    state_signed = SERIALIZER.dumps(state)

    print(random_state, state, state_signed)
    assert isinstance(state, str)
    assert isinstance(state_signed, str)

    url = api_client.build_authorization_url(show_dialog=False, state=state)

    response = RedirectResponse(url=url)
    response.set_cookie(
        key="spotify_auth_state", value=state_signed, max_age=FIVE_MINUTES
    )
    return response


@router.get("/callback")
async def callback(request: Request):
    cookies = request.cookies
    if "spotify_auth_state" not in cookies:
        return "No state cookie found", 400

    signed_state = cookies["spotify_auth_state"]
    try:
        state: str = SERIALIZER.loads(signed_state)
    except BadSignature:
        return "Invalid state", 400

    if state != request.query_params["state"]:
        return "Invalid state", 400

    code = request.query_params.get("code")
    if not code:
        return "No code", 400

    auth_token = await api_client.get_auth_token_with_code(code)
    _, user_id = SERIALIZER.loads(state)

    access_token = auth_token.access_token
    refresh_token = auth_token.refresh_token
    expiry_time = datetime.fromtimestamp(auth_token.activation_time + 3400, tz=UTC)

    try:
        user = await User.objects.get(id=user_id)
    except NoMatch:
        await User.objects.create(
            id=user_id,
            spotify_access_token=access_token,
            spotify_refresh_token=refresh_token,
            spotify_token_expires=expiry_time,
        )
    else:
        user.spotify_access_token = access_token
        user.spotify_refresh_token = refresh_token
        user.spotify_token_expires = expiry_time
        await user.update()

    return {"code": code, "state": state}
