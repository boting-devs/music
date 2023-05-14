from datetime import UTC, datetime
from os import environ
from secrets import token_urlsafe

from async_spotify import SpotifyApiClient
from async_spotify.authentification.authorization_flows import AuthorizationCodeFlow
from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRouter
from fastapi.templating import Jinja2Templates
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
templates = Jinja2Templates(directory="api/templates")


async def init() -> None:
    await api_client.create_new_client()


async def deinit() -> None:
    await api_client.close_client()


@router.get("/authorize")
async def authorize(request: Request):
    signed_user_id = request.query_params["user"]
    user_id: int = SERIALIZER.loads(signed_user_id)

    random_state = token_urlsafe(nbytes=12)
    state = SERIALIZER.dumps((random_state, user_id))
    state_signed = SERIALIZER.dumps(state)

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
        return templates.TemplateResponse(
            "linked.jinja2",
            {"request": request, "error": "No cookie found."},
            status_code=400,
        )

    signed_state = cookies["spotify_auth_state"]
    try:
        state: str = SERIALIZER.loads(signed_state)
    except BadSignature:
        return templates.TemplateResponse(
            "linked.jinja2",
            {"request": request, "error": "Cookie signature invalid."},
            status_code=400,
        )

    try:
        state_param = request.query_params["state"]
    except KeyError:
        return templates.TemplateResponse(
            "linked.jinja2",
            {"request": request, "error": "No state parameter."},
            status_code=400,
        )

    if state != state_param:
        return templates.TemplateResponse(
            "linked.jinja2",
            {"request": request, "error": "State parameter invalid."},
            status_code=400,
        )

    code = request.query_params.get("code")
    if not code:
        return templates.TemplateResponse(
            "linked.jinja2",
            {"request": request, "error": "No code parameter."},
            status_code=400,
        )

    auth_token = await api_client.get_auth_token_with_code(code)
    _, user_id = SERIALIZER.loads(state)

    access_token = auth_token.access_token
    refresh_token = auth_token.refresh_token
    activation_time = datetime.fromtimestamp(auth_token.activation_time, tz=UTC)

    try:
        user = await User.objects.get(id=user_id)
    except NoMatch:
        await User.objects.create(
            id=user_id,
            spotify_access_token=access_token,
            spotify_refresh_token=refresh_token,
            spotify_activation_time=activation_time,
        )
    else:
        user.spotify_access_token = access_token
        user.spotify_refresh_token = refresh_token
        user.spotify_activation_time = activation_time
        await user.update()

    return templates.TemplateResponse(
        "linked.jinja2",
        {"request": request},
    )


@router.get("/test")
async def tmp(request: Request):
    return templates.TemplateResponse(
        "linked.jinja2",
        {"request": request},
    )
