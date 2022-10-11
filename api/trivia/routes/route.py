from http import HTTPStatus

from flasgger import swag_from
from flask import Blueprint, abort, request

from api.trivia.models.models import Question

trivia = Blueprint("trivia", __name__)


@trivia.route("/questions", methods=["GET"])
def get_questions():

    # paginate questions
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    start = (page - 1) * limit
    end = start + limit

    questions = Question.query.all()
    formatted_questions = [question.format() for question in questions]

    if not formatted_questions:
        abort(HTTPStatus.NOT_FOUND)

    return {
        "success": True,
        "questions": formatted_questions[start:end],
        "total_questions": len(formatted_questions),
    }


@trivia.route("/questions", methods=["POST"])
def post_questions():

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


@trivia.route("/categories/<int:category_id>/questions", methods=["GET"])
def get_questions_by_category(category_id):

    # paginate questions
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    start = (page - 1) * limit
    end = start + limit

    questions = Question.query.filter_by(category_id=category_id).all()
    formatted_questions = [question.format() for question in questions]

    if not formatted_questions:
        abort(HTTPStatus.NOT_FOUND)

    return {
        "success": True,
        "questions": formatted_questions[start:end],
        "total_questions": len(formatted_questions),
        "current_category": category_id,
    }
