import datetime
import uuid
from http import HTTPStatus

import jwt
from flasgger import swag_from
from flask import Blueprint, abort
from flask import current_app as app
from flask import jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from api.trivia.auth.auth import token_required
from api.trivia.models.models import Category, Question, User
from caching import cache

trivia = Blueprint("trivia", __name__)


@trivia.route("/questions", methods=["GET"])
@token_required
@cache.cached(timeout=50)
def get_questions(current_user):

    # paginate questions using paginate method from SQLAlchemy
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
@token_required
def post_questions(current_user):

    # post a new question
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


@cache.cached(timeout=50)
@trivia.route("/categories/<int:category_id>/questions", methods=["GET"])
def get_questions_by_category(category_id):

    # paginate questions paginate method from SQLAlchemy
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
