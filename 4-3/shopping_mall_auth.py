from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from html import escape
from secrets import token_urlsafe
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings
from urllib.parse import urlencode


class Settings(BaseSettings):
    """Configuration pulled from environment variables."""

    base_url: AnyHttpUrl = "http://localhost:8000"
    kakao_client_id: str = "YOUR_KAKAO_REST_API_KEY"
    kakao_client_secret: str = "YOUR_KAKAO_CLIENT_SECRET"
    naver_client_id: str = "YOUR_NAVER_CLIENT_ID"
    naver_client_secret: str = "YOUR_NAVER_CLIENT_SECRET"
    google_client_id: str = "YOUR_GOOGLE_CLIENT_ID"
    google_client_secret: str = "YOUR_GOOGLE_CLIENT_SECRET"
    frontend_redirect_url: Optional[AnyHttpUrl] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


@dataclass(frozen=True)
class ProviderConfig:
    slug: str
    display_name: str
    authorize_endpoint: str
    token_endpoint: str
    profile_endpoint: str
    scopes: List[str]
    client_id_attr: str
    client_secret_attr: str
    callback_path: str
    extra_auth_params: Dict[str, str] = field(default_factory=dict)
    extra_token_params: Dict[str, str] = field(default_factory=dict)

    def redirect_uri(self, settings: Settings) -> str:
        base = str(settings.base_url).rstrip("/")
        path = self.callback_path if self.callback_path.startswith("/") else f"/{self.callback_path}"
        return f"{base}{path}"


class StateStore:
    """In-memory store that issues and validates short-lived OAuth state tokens."""

    def __init__(self, ttl_seconds: int = 600) -> None:
        self._ttl = ttl_seconds
        self._states: Dict[str, tuple[str, datetime]] = {}

    def issue(self, provider_slug: str) -> str:
        self._purge_expired()
        state = token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self._ttl)
        self._states[state] = (provider_slug, expires_at)
        return state

    def consume(self, state: Optional[str], provider_slug: str) -> bool:
        if not state:
            return False
        self._purge_expired()
        stored = self._states.pop(state, None)
        if not stored:
            return False
        stored_provider, expires_at = stored
        if stored_provider != provider_slug:
            return False
        if expires_at < datetime.now(timezone.utc):
            return False
        return True

    def _purge_expired(self) -> None:
        now = datetime.now(timezone.utc)
        expired_keys = [key for key, (_, expiry) in self._states.items() if expiry < now]
        for key in expired_keys:
            self._states.pop(key, None)


def normalize_profile(provider_slug: str, payload: Dict[str, Any], token_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Convert provider specific payloads into a consistent structure."""

    normalized: Dict[str, Any] = {
        "provider": provider_slug,
        "token_expires_in": token_payload.get("expires_in"),
        "raw_profile": payload,
    }

    if provider_slug == "google":
        normalized.update(
            {
                "id": payload.get("id") or payload.get("sub"),
                "email": payload.get("email"),
                "name": payload.get("name") or payload.get("given_name"),
                "avatar": payload.get("picture"),
            }
        )
    elif provider_slug == "kakao":
        account = payload.get("kakao_account") or {}
        profile = account.get("profile") or {}
        normalized.update(
            {
                "id": payload.get("id"),
                "email": account.get("email"),
                "name": profile.get("nickname"),
                "avatar": profile.get("profile_image_url") or profile.get("thumbnail_image_url"),
            }
        )
    elif provider_slug == "naver":
        response_data = payload.get("response") or {}
        normalized.update(
            {
                "id": response_data.get("id"),
                "email": response_data.get("email"),
                "name": response_data.get("name") or response_data.get("nickname"),
                "avatar": response_data.get("profile_image"),
            }
        )
    else:
        normalized.update(
            {
                "id": payload.get("id"),
                "email": payload.get("email"),
                "name": payload.get("name"),
            }
        )

    return normalized


PROVIDERS: List[ProviderConfig] = [
    ProviderConfig(
        slug="kakao",
        display_name="Kakao",
        authorize_endpoint="https://kauth.kakao.com/oauth/authorize",
        token_endpoint="https://kauth.kakao.com/oauth/token",
        profile_endpoint="https://kapi.kakao.com/v2/user/me",
        scopes=["profile_nickname", "profile_image", "account_email"],
        client_id_attr="kakao_client_id",
        client_secret_attr="kakao_client_secret",
        callback_path="/auth/kakao/callback",
        extra_auth_params={"prompt": "login"},
    ),
    ProviderConfig(
        slug="naver",
        display_name="Naver",
        authorize_endpoint="https://nid.naver.com/oauth2.0/authorize",
        token_endpoint="https://nid.naver.com/oauth2.0/token",
        profile_endpoint="https://openapi.naver.com/v1/nid/me",
        scopes=["name", "email"],
        client_id_attr="naver_client_id",
        client_secret_attr="naver_client_secret",
        callback_path="/auth/naver/callback",
    ),
    ProviderConfig(
        slug="google",
        display_name="Google",
        authorize_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
        token_endpoint="https://oauth2.googleapis.com/token",
        profile_endpoint="https://www.googleapis.com/oauth2/v2/userinfo",
        scopes=["openid", "email", "profile"],
        client_id_attr="google_client_id",
        client_secret_attr="google_client_secret",
        callback_path="/auth/google/callback",
        extra_auth_params={
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "consent",
        },
    ),
]


class OAuthManager:
    """Handles OAuth provider lookups and API calls."""

    def __init__(self, settings: Settings, providers: List[ProviderConfig]) -> None:
        self._settings = settings
        self._providers = {provider.slug: provider for provider in providers}

    def list_providers(self) -> List[ProviderConfig]:
        return list(self._providers.values())

    def get_provider(self, slug: str) -> ProviderConfig:
        provider = self._providers.get(slug.lower())
        if not provider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown provider: {slug}")
        return provider

    def _get_credentials(self, provider: ProviderConfig) -> Dict[str, str]:
        client_id = getattr(self._settings, provider.client_id_attr, "")
        client_secret = getattr(self._settings, provider.client_secret_attr, "")
        if not client_id or client_id.startswith("YOUR_"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{provider.display_name} client id is not configured.",
            )
        if not client_secret or client_secret.startswith("YOUR_"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{provider.display_name} client secret is not configured.",
            )
        return {"client_id": client_id, "client_secret": client_secret}

    def build_authorize_url(self, provider: ProviderConfig, state: str) -> str:
        creds = self._get_credentials(provider)
        params = {
            "response_type": "code",
            "client_id": creds["client_id"],
            "redirect_uri": provider.redirect_uri(self._settings),
            "state": state,
        }
        if provider.scopes:
            params["scope"] = " ".join(provider.scopes)
        params.update(provider.extra_auth_params)
        return f"{provider.authorize_endpoint}?{urlencode(params)}"

    async def exchange_code(self, provider: ProviderConfig, code: str, state: Optional[str]) -> Dict[str, Any]:
        creds = self._get_credentials(provider)
        data = {
            "grant_type": "authorization_code",
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "code": code,
            "redirect_uri": provider.redirect_uri(self._settings),
        }
        if state and provider.slug == "naver":
            data["state"] = state
        data.update(provider.extra_token_params)
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(provider.token_endpoint, data=data)
        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "message": "Token exchange failed",
                    "provider": provider.slug,
                    "response": response.text,
                },
            )
        try:
            token_payload = response.json()
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"message": "Token response was not JSON", "provider": provider.slug},
            ) from exc
        if "access_token" not in token_payload:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "message": "Token response missing access token",
                    "provider": provider.slug,
                    "payload": token_payload,
                },
            )
        return token_payload

    async def fetch_profile(self, provider: ProviderConfig, token_payload: Dict[str, Any]) -> Dict[str, Any]:
        access_token = token_payload.get("access_token")
        token_type = token_payload.get("token_type", "Bearer")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"message": "Missing access token", "provider": provider.slug},
            )
        headers = {"Authorization": f"{token_type.title()} {access_token}"}
        if provider.slug == "kakao":
            headers["Authorization"] = f"Bearer {access_token}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(provider.profile_endpoint, headers=headers)
        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "message": "Profile fetch failed",
                    "provider": provider.slug,
                    "response": response.text,
                },
            )
        try:
            profile_payload = response.json()
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"message": "Profile response was not JSON", "provider": provider.slug},
            ) from exc
        return normalize_profile(provider.slug, profile_payload, token_payload)


app = FastAPI(
    title="Shopping Mall Social Login API",
    description=(
        "FastAPI backend for an apparel, cosmetics, and fragrance shopping mall "
        "supporting Kakao, Naver, and Google login flows."
    ),
    version="0.1.0",
)

settings = get_settings()
oauth_manager = OAuthManager(settings, PROVIDERS)
state_store = StateStore(ttl_seconds=600)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    links = []
    for provider in oauth_manager.list_providers():
        links.append(
            {
                "label": provider.display_name,
                "href": request.url_for("start_login", provider_slug=provider.slug),
            }
        )
    link_items = "".join(
        f"<li><a class=\"provider-link\" href=\"{link['href']}\">{link['label']} Login</a></li>"
        for link in links
    )
    body = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<title>Shopping Mall Social Login</title>
<style>
body {{
    margin: 0;
    padding: 40px;
    font-family: 'Segoe UI', Arial, sans-serif;
    background: linear-gradient(135deg, #fce7f3, #eff6ff);
}}
main {{
    max-width: 760px;
    margin: 0 auto;
    background: #ffffffdd;
    border-radius: 16px;
    padding: 36px;
    box-shadow: 0 20px 45px rgba(15, 23, 42, 0.15);
}}
h1 {{
    margin-top: 0;
    font-size: 2.2rem;
    color: #111827;
}}
p.description {{
    color: #374151;
    line-height: 1.6;
}}
ul.providers {{
    list-style: none;
    padding: 0;
    margin: 32px 0 0 0;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
}}
ul.providers li {{
    text-align: center;
}}
a.provider-link {{
    display: inline-block;
    width: 100%;
    padding: 14px 18px;
    border-radius: 999px;
    text-decoration: none;
    font-weight: 600;
    color: #ffffff;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    box-shadow: 0 12px 25px rgba(79, 70, 229, 0.35);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}
a.provider-link:hover {{
    transform: translateY(-3px);
    box-shadow: 0 18px 35px rgba(79, 70, 229, 0.45);
}}
footer {{
    margin-top: 36px;
    font-size: 0.85rem;
    color: #6b7280;
    text-align: center;
}}
</style>
</head>
<body>
<main>
<h1>Shopping Mall Social Login Demo</h1>
<p class=\"description\">Example FastAPI backend for a fashion, beauty, and fragrance shopping mall. Launch an OAuth login flow with one of the providers below.</p>
<ul class=\"providers\">{link_items}</ul>
<footer>Configure each provider client id and secret through environment variables before using this demo.</footer>
</main>
</body>
</html>"""
    return HTMLResponse(content=body)


@app.get("/auth/{provider_slug}/login", name="start_login")
async def start_login(provider_slug: str) -> RedirectResponse:
    provider = oauth_manager.get_provider(provider_slug)
    state = state_store.issue(provider.slug)
    authorize_url = oauth_manager.build_authorize_url(provider, state)
    return RedirectResponse(url=authorize_url, status_code=status.HTTP_302_FOUND)


@app.get("/auth/{provider_slug}/callback", name="auth_callback", response_class=HTMLResponse)
async def auth_callback(
    provider_slug: str,
    request: Request,
    code: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None),
    error: Optional[str] = Query(default=None),
    error_description: Optional[str] = Query(default=None),
) -> HTMLResponse:
    provider = oauth_manager.get_provider(provider_slug)
    if error:
        detail = f"{error}: {error_description}" if error_description else error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    if not state_store.consume(state, provider.slug):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OAuth state.")
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing authorization code.")

    token_payload = await oauth_manager.exchange_code(provider, code, state)
    profile = await oauth_manager.fetch_profile(provider, token_payload)

    if settings.frontend_redirect_url:
        redirect_target = str(settings.frontend_redirect_url)
        query = urlencode(
            {
                "provider": provider.slug,
                "id": profile.get("id") or "",
                "name": profile.get("name") or "",
                "email": profile.get("email") or "",
            }
        )
        return RedirectResponse(url=f"{redirect_target}?{query}", status_code=status.HTTP_302_FOUND)

    pretty_profile = json.dumps(profile, indent=2)
    escaped_profile = escape(pretty_profile)
    body = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<title>{provider.display_name} Login Success</title>
<style>
body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    margin: 0;
    padding: 40px;
    background: #f3f4f6;
}}
main {{
    max-width: 760px;
    margin: 0 auto;
    background: #ffffff;
    border-radius: 16px;
    padding: 36px;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.1);
}}
h1 {{
    margin-top: 0;
    color: #111827;
}}
pre {{
    background: #111827;
    color: #f3f4f6;
    padding: 20px;
    border-radius: 12px;
    overflow-x: auto;
}}
a {{
    display: inline-block;
    margin-top: 24px;
    text-decoration: none;
    color: #2563eb;
}}
</style>
</head>
<body>
<main>
<h1>{provider.display_name} login succeeded</h1>
<p>Use the JSON payload below to create a session or issue your own token from the shopping mall frontend.</p>
<pre>{escaped_profile}</pre>
<a href=\"{request.url_for('home')}\">Back to home</a>
</main>
</body>
</html>"""
    return HTMLResponse(content=body)


@app.get("/healthz")
async def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("shopping_mall_auth:app", host="0.0.0.0", port=8000, reload=True)
