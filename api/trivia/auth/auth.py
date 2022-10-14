import json
from functools import wraps
from http import HTTPStatus
from urllib.request import urlopen

import jwt
from flask import _request_ctx_stack
from flask import current_app as app
from flask import request

from api.trivia.utils.error import AuthError


def get_token_auth_header():
    "Obtain the Access Token from the Authorization Header"
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError(
            {
                "code": "authorization_header_missing",
                "description": "Authorization header is expected.",
            },
            HTTPStatus.UNAUTHORIZED,
        )
    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Authorization header must start with Bearer.",
            },
            HTTPStatus.UNAUTHORIZED,
        )

    elif len(parts) == 1:
        raise AuthError(
            {"code": "invalid_header", "description": "Token not found."},
            HTTPStatus.UNAUTHORIZED,
        )

    elif len(parts) > 2:
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Authorization header must be Bearer token.",
            },
            HTTPStatus.UNAUTHORIZED,
        )

    return parts[1]


def require_auth(f):
    "Validate the Access Token"

    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_auth_header()
        jsonurl = urlopen(f"https://{app.config['AUTH0_DOMAIN']}/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
        if rsa_key:
            try:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=app.config["ALGORITHMS"],
                    audience=app.config["API_AUDIENCE"],
                    issuer=f"https://{app.config['AUTH0_DOMAIN']}/",
                    options={"verify_signature": False},
                )
            except jwt.ExpiredSignatureError:
                raise AuthError(
                    {"code": "token_expired", "description": "Token expired."},
                    HTTPStatus.UNAUTHORIZED,
                )
            except jwt.JWTClaimsError:
                raise AuthError(
                    {
                        "code": "invalid_claims",
                        "description": "Incorrect claims. Please, check the audience and issuer.",
                    },
                    HTTPStatus.UNAUTHORIZED,
                )
            except Exception:
                raise AuthError(
                    {
                        "code": "invalid_header",
                        "description": "Unable to parse authentication token.",
                    },
                    HTTPStatus.BAD_REQUEST,
                )

            _request_ctx_stack.top.current_user = payload
            return f(*args, **kwargs)

        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Unable to find the appropriate key.",
            },
            HTTPStatus.BAD_REQUEST,
        )

    return decorated


def requires_scope(required_scope):
    "Determines if the required scope is present in the Access Token"
    token = get_token_auth_header()
    unverified_claims = jwt.get_unverified_claims(token)
    if unverified_claims.get("scope"):
        token_scopes = unverified_claims["scope"].split()
        for token_scope in token_scopes:
            if token_scope == required_scope:
                return True
    return False
