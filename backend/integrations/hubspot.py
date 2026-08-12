import json
import os
import secrets
from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse

from integrations.integration_item import IntegrationItem

from redis_client import (
    add_key_value_redis,
    get_value_redis,
    delete_key_redis,
)


# ============================================================
# Configuration
# ============================================================

load_dotenv()

CLIENT_ID = os.getenv("HUBSPOT_CLIENT_ID")
CLIENT_SECRET = os.getenv("HUBSPOT_CLIENT_SECRET")

REDIRECT_URI = os.getenv(
    "HUBSPOT_REDIRECT_URI",
    "http://localhost:8000/integrations/hubspot/oauth2callback",
)

AUTHORIZATION_URL = "https://app.hubspot.com/oauth/authorize"

TOKEN_URL = "https://api.hubapi.com/oauth/2026-03/token"

SCOPES = "oauth crm.objects.contacts.read"


# ============================================================
# OAuth Authorization
# ============================================================

async def authorize_hubspot(user_id, org_id):
    """
    Generate the HubSpot OAuth authorization URL
    and store OAuth state temporarily in Redis.
    """

    if not CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="HubSpot client ID is not configured.",
        )

    state = secrets.token_urlsafe(32)

    state_data = {
        "user_id": user_id,
        "org_id": org_id,
    }

    await add_key_value_redis(
        f"hubspot_state:{state}",
        json.dumps(state_data),
        expire=600,
    )

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
    }

    return f"{AUTHORIZATION_URL}?{urlencode(params)}"


# ============================================================
# OAuth Callback
# ============================================================

async def oauth2callback_hubspot(request: Request):
    """
    Handle HubSpot OAuth callback.

    Exchanges the authorization code for an access token
    and refresh token.
    """

    error = request.query_params.get("error")

    if error:
        error_description = request.query_params.get(
            "error_description",
            error,
        )

        raise HTTPException(
            status_code=400,
            detail=error_description,
        )

    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code:
        raise HTTPException(
            status_code=400,
            detail="Authorization code not found.",
        )

    if not state:
        raise HTTPException(
            status_code=400,
            detail="State not found.",
        )

    # --------------------------------------------------------
    # Validate state
    # --------------------------------------------------------

    saved_state = await get_value_redis(
        f"hubspot_state:{state}"
    )

    if not saved_state:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired state.",
        )

    state_data = json.loads(saved_state)

    user_id = state_data.get("user_id")
    org_id = state_data.get("org_id")

    if not user_id or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid state data.",
        )

    if not CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="HubSpot client ID is not configured.",
        )

    if not CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="HubSpot client secret is not configured.",
        )

    # --------------------------------------------------------
    # Exchange authorization code for tokens
    # --------------------------------------------------------

    async with httpx.AsyncClient(timeout=20.0) as client:

        response = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
            },
            headers={
                "Content-Type": (
                    "application/x-www-form-urlencoded"
                ),
            },
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=(
                "HubSpot OAuth token exchange failed: "
                f"{response.text}"
            ),
        )

    credentials = response.json()

    # --------------------------------------------------------
    # Store when the access token was obtained
    # --------------------------------------------------------

    expires_in = credentials.get("expires_in", 1800)

    credentials["obtained_at"] = int(
        datetime.now(timezone.utc).timestamp()
    )

    credentials["expires_at"] = (
        credentials["obtained_at"] + expires_in
    )

    # --------------------------------------------------------
    # Delete OAuth state
    # --------------------------------------------------------

    await delete_key_redis(
        f"hubspot_state:{state}"
    )

    # --------------------------------------------------------
    # Temporarily store credentials
    # --------------------------------------------------------

    await add_key_value_redis(
        f"hubspot_credentials:{org_id}:{user_id}",
        json.dumps(credentials),
        expire=600,
    )

    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """

    return HTMLResponse(
        content=close_window_script
    )


# ============================================================
# Get Credentials
# ============================================================

async def get_hubspot_credentials(user_id, org_id):
    """
    Retrieve HubSpot OAuth credentials from Redis.
    """

    credentials = await get_value_redis(
        f"hubspot_credentials:{org_id}:{user_id}"
    )

    if not credentials:
        raise HTTPException(
            status_code=400,
            detail="No credentials found.",
        )

    if isinstance(credentials, bytes):
        credentials = credentials.decode("utf-8")

    credentials = json.loads(credentials)

    if not credentials:
        raise HTTPException(
            status_code=400,
            detail="No credentials found.",
        )

    await delete_key_redis(
        f"hubspot_credentials:{org_id}:{user_id}"
    )

    return credentials


# ============================================================
# Refresh Access Token
# ============================================================

async def refresh_hubspot_access_token(
    refresh_token: str,
):
    """
    Get a new HubSpot access token using the refresh token.
    """

    if not CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="HubSpot client ID is not configured.",
        )

    if not CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="HubSpot client secret is not configured.",
        )

    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail=(
                "HubSpot refresh token is missing. "
                "Please reconnect HubSpot."
            ),
        )

    async with httpx.AsyncClient(timeout=20.0) as client:

        response = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": refresh_token,
            },
            headers={
                "Content-Type": (
                    "application/x-www-form-urlencoded"
                ),
            },
        )

    if response.status_code != 200:

        error_data = {}

        try:
            error_data = response.json()
        except Exception:
            pass

        error_type = error_data.get("error")

        if error_type == "invalid_grant":

            raise HTTPException(
                status_code=401,
                detail=(
                    "HubSpot refresh token is invalid or "
                    "revoked. Please reconnect HubSpot."
                ),
            )

        raise HTTPException(
            status_code=response.status_code,
            detail=(
                "Failed to refresh HubSpot access token: "
                f"{response.text}"
            ),
        )

    new_credentials = response.json()

    # HubSpot normally returns the refresh token again,
    # but keep the old one if it doesn't.
    if not new_credentials.get("refresh_token"):
        new_credentials["refresh_token"] = refresh_token

    expires_in = new_credentials.get(
        "expires_in",
        1800,
    )

    obtained_at = int(
        datetime.now(timezone.utc).timestamp()
    )

    new_credentials["obtained_at"] = obtained_at

    new_credentials["expires_at"] = (
        obtained_at + expires_in
    )

    return new_credentials


# ============================================================
# Get Valid Access Token
# ============================================================

async def get_valid_hubspot_credentials(credentials):
    """
    Check whether the HubSpot access token is still valid.

    Refresh it automatically when it is expired or about
    to expire.
    """

    if isinstance(credentials, bytes):
        credentials = credentials.decode("utf-8")

    if isinstance(credentials, str):
        credentials = json.loads(credentials)

    if not credentials:
        raise HTTPException(
            status_code=400,
            detail="No HubSpot credentials provided.",
        )

    access_token = credentials.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="HubSpot access token not found.",
        )

    # --------------------------------------------------------
    # Determine expiration
    # --------------------------------------------------------

    expires_at = credentials.get("expires_at")

    if expires_at is None:

        obtained_at = credentials.get("obtained_at")

        if obtained_at is not None:

            expires_in = credentials.get(
                "expires_in",
                1800,
            )

            expires_at = (
                obtained_at + expires_in
            )

    # --------------------------------------------------------
    # If we don't know expiration, use current token.
    # --------------------------------------------------------

    if expires_at is None:
        return credentials

    current_timestamp = int(
        datetime.now(timezone.utc).timestamp()
    )

    # Refresh 5 minutes before expiration.
    refresh_buffer = 300

    token_needs_refresh = (
        current_timestamp
        >= expires_at - refresh_buffer
    )

    if not token_needs_refresh:
        return credentials

    # --------------------------------------------------------
    # Refresh token
    # --------------------------------------------------------

    print(
        "HubSpot access token expired or "
        "about to expire. Refreshing..."
    )

    new_credentials = (
        await refresh_hubspot_access_token(
            credentials.get("refresh_token")
        )
    )

    return new_credentials


# ============================================================
# IntegrationItem Metadata
# ============================================================

def create_integration_item_metadata_object(
    response_json
) -> IntegrationItem:
    """
    Convert a HubSpot contact response into an
    IntegrationItem.
    """

    properties = response_json.get(
        "properties",
        {},
    )

    first_name = (
        properties.get("firstname")
        or ""
    )

    last_name = (
        properties.get("lastname")
        or ""
    )

    full_name = (
        f"{first_name} {last_name}"
    ).strip()

    if not full_name:

        full_name = (
            properties.get("email")
            or "Unnamed Contact"
        )

    created_at = response_json.get(
        "createdAt"
    )

    updated_at = response_json.get(
        "updatedAt"
    )

    creation_time = None
    last_modified_time = None

    if created_at:

        try:

            creation_time = datetime.fromisoformat(
                created_at.replace(
                    "Z",
                    "+00:00",
                )
            )

        except ValueError:

            creation_time = None

    if updated_at:

        try:

            last_modified_time = datetime.fromisoformat(
                updated_at.replace(
                    "Z",
                    "+00:00",
                )
            )

        except ValueError:

            last_modified_time = None

    return IntegrationItem(
        id=response_json.get("id"),
        type="Contact",
        directory=False,
        name=full_name,
        creation_time=creation_time,
        last_modified_time=last_modified_time,
        url=response_json.get("url"),
        visibility=True,
    )


# ============================================================
# Get HubSpot Contacts
# ============================================================

async def get_items_hubspot(
    credentials
) -> list[IntegrationItem]:
    """
    Retrieve HubSpot contacts.

    Automatically refreshes the access token when
    necessary.
    """

    # --------------------------------------------------------
    # Parse credentials
    # --------------------------------------------------------

    if isinstance(credentials, bytes):
        credentials = credentials.decode("utf-8")

    if isinstance(credentials, str):
        credentials = json.loads(credentials)

    if not credentials:

        raise HTTPException(
            status_code=400,
            detail="No HubSpot credentials provided.",
        )

    # --------------------------------------------------------
    # Refresh token if necessary
    # --------------------------------------------------------

    credentials = (
        await get_valid_hubspot_credentials(
            credentials
        )
    )

    access_token = credentials.get(
        "access_token"
    )

    if not access_token:

        raise HTTPException(
            status_code=401,
            detail="HubSpot access token not found.",
        )

    # --------------------------------------------------------
    # HubSpot Contacts API
    # --------------------------------------------------------

    url = (
        "https://api.hubapi.com/"
        "crm/v3/objects/contacts"
    )

    params = {
        "limit": 100,
        "properties": (
            "firstname,"
            "lastname,"
            "email,"
            "phone,"
            "company"
        ),
    }

    headers = {
        "Authorization": (
            f"Bearer {access_token}"
        ),
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(
        timeout=20.0
    ) as client:

        response = await client.get(
            url,
            headers=headers,
            params=params,
        )

    # --------------------------------------------------------
    # Handle expired/invalid token
    # --------------------------------------------------------

    if response.status_code == 401:

        refresh_token = credentials.get(
            "refresh_token"
        )

        if not refresh_token:

            raise HTTPException(
                status_code=401,
                detail=(
                    "HubSpot access token expired. "
                    "Please reconnect HubSpot."
                ),
            )

        print(
            "HubSpot returned 401. "
            "Attempting token refresh..."
        )

        credentials = (
            await refresh_hubspot_access_token(
                refresh_token
            )
        )

        access_token = credentials.get(
            "access_token"
        )

        headers["Authorization"] = (
            f"Bearer {access_token}"
        )

        async with httpx.AsyncClient(
            timeout=20.0
        ) as client:

            response = await client.get(
                url,
                headers=headers,
                params=params,
            )

    # --------------------------------------------------------
    # Handle API errors
    # --------------------------------------------------------

    if response.status_code != 200:

        raise HTTPException(
            status_code=response.status_code,
            detail=(
                "Failed to retrieve HubSpot "
                "contacts: "
                f"{response.text}"
            ),
        )

    # --------------------------------------------------------
    # Convert results
    # --------------------------------------------------------

    response_json = response.json()

    results = response_json.get(
        "results",
        [],
    )

    integration_items = []

    for result in results:

        integration_item = (
            create_integration_item_metadata_object(
                result
            )
        )

        integration_items.append(
            integration_item
        )

    print(
        "HubSpot Integration Items:",
        integration_items,
    )

    return integration_items