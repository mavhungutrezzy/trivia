from functools import wraps
from http import HTTPStatus

import jwt
from flask import current_app as app
from flask import jsonify, request

from api.trivia.models.models import User


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")
            print(token)
        if not token:
            return (
                jsonify(
                    {
                        "message": "Token is missing!",
                        "data": None,
                        "error": "Unauthorized",
                    }
                ),
                HTTPStatus.UNAUTHORIZED,
            )
        try:
            data = jwt.decode(token[0], app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user = User.query.filter_by(public_id=data["public_id"]).first()
            if current_user is None:
                return (
                    jsonify(
                        {
                            "message": "Token is invalid!",
                            "data": None,
                            "error": "Unauthorized",
                        }
                    ),
                    HTTPStatus.UNAUTHORIZED,
                )
        except Exception as e:
            return (
                jsonify(
                    {"message": "Something went wrong", "data": None, "error": str(e)}
                ),
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return f(current_user, *args, **kwargs)

    return decorated
