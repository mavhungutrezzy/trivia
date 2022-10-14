import datetime
import uuid
from http import HTTPStatus

import jwt
from flasgger import swag_from
from flask import Blueprint, abort
from flask import current_app as app
from flask import jsonify, request
from flask_cors import cross_origin
from werkzeug.security import check_password_hash, generate_password_hash

from api.trivia.auth.auth import require_auth
from api.trivia.models.models import Category, Question, User
from api.trivia.utils.caching import cache
from api.trivia.utils.error import AuthError

trivia = Blueprint("trivia", __name__)


@trivia.errorhandler(AuthError)
def handle_auth_error(exception):
    "Handles Authentication Errors"
    response = jsonify(exception.error)
    response.status_code = exception.status_code
    return response


@trivia.route("/questions", methods=["GET"])
@cache.cached(timeout=50)
@cross_origin(headers=["Content-Type", "Authorization"])
@require_auth
def get_questions():

    # Query the database for all questions and paginate the results
    questions = Question.query.paginate(
        page=request.args.get("page", 1, type=int),
        per_page=request.args.get("per_page", 1, type=int),
        error_out=False,
    )
    if not questions.items:
        abort(HTTPStatus.NOT_FOUND)

    return jsonify(
        {
            "message": "Questions retrieved successfully",
            "data": {
                "questions": [question.format() for question in questions.items],
                "total_questions": questions.total,
                "categories": {
                    category.id: category.name for category in Category.query.all()
                },
                "current_category": None,
            },
        }
    )


@trivia.route("/questions", methods=["POST"])
@cross_origin(headers=["Content-Type", "Authorization"])
@require_auth
def post_questions():

    # Get the request data
    body = request.get_json()
    new_question = body.get("question", None)
    new_answer = body.get("answer", None)
    new_difficulty = body.get("difficulty", None)
    new_category = body.get("category", None)

    try:
        if "" in {new_question, new_answer, new_difficulty, new_category}:
            abort(HTTPStatus.BAD_REQUEST)

        question = Question(
            question=new_question,
            answer=new_answer,
            difficulty=new_difficulty,
            category_id=new_category,
        )
        question.add()

        return {"success": True, "created": question.id}
    except Exception:
        abort(HTTPStatus.BAD_REQUEST)


@trivia.route("/categories/<int:category_id>/questions", methods=["GET"])
@cache.cached(timeout=50)
@cross_origin(headers=["Content-Type", "Authorization"])
@require_auth
def get_questions_by_category(category_id):

    # Query the database for all questions and paginate the results
    questions = Question.query.filter_by(category_id=category_id).paginate(
        page=request.args.get("page", 1, type=int),
        per_page=request.args.get("per_page", 1, type=int),
        error_out=False,
    )
    if not questions.items:
        abort(HTTPStatus.NOT_FOUND)

    return jsonify(
        {
            "message": "Questions retrieved successfully",
            "data": {
                "questions": [question.format() for question in questions.items],
                "total_questions": questions.total,
                "current_category": category_id,
            },
        }
    )


@trivia.route("/questions/<int:question_id>", methods=["DELETE"])
def delete_question(question_id):
    """This endpoint deletes a question using a question ID."""
    try:
        question = Question.query.filter_by(id=question_id).one_or_none()
        if question is None:
            abort(HTTPStatus.NOT_FOUND)
        question.delete()
        return jsonify(
            {
                "message": "Question deleted successfully",
                "data": {"deleted": question_id},
            }
        )
    except Exception:
        abort(HTTPStatus.BAD_REQUEST)


@trivia.route("/users/login", methods=["POST"])
def login():
    # login a user with email and password
    body = request.get_json()
    email = body.get("email", None)
    password = body.get("password", None)

    if not email or not password:
        abort(HTTPStatus.BAD_REQUEST)

    user = User.query.filter_by(email=email).first()
    if not user:
        abort(HTTPStatus.NOT_FOUND)

    if check_password_hash(user.password, password):
        # generate the JWT token
        token = jwt.encode(
            {
                "public_id": user.public_id,
                "exp": datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(minutes=30),
            },
            app.config["SECRET_KEY"],
            algorithm="HS256",
        )
        return (
            jsonify(
                {
                    "token": token,
                }
            ),
            HTTPStatus.CREATED,
        )
    else:
        abort(HTTPStatus.UNAUTHORIZED)


@trivia.route("/users/register", methods=["POST"])
def register():
    body = request.get_json()
    email = body.get("email", None)
    password = body.get("password", None)

    if not email or not password:
        abort(HTTPStatus.BAD_REQUEST)

    if user := User.query.filter_by(email=email).first():
        return (
            jsonify(
                {"success": False, "message": "User already exists. Please Log in."}
            ),
            HTTPStatus.CONFLICT,
        )
    user = User(
        public_id=str(uuid.uuid4()),
        email=email,
        password=generate_password_hash(password),
    )
    user.add()
    return (
        jsonify({"success": True, "message": "User created successfully"}),
        HTTPStatus.CREATED,
    )
