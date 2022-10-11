from flasgger import Swagger
from flask import Flask
from flask_migrate import Migrate

from database import database

migrate = Migrate()

from api.trivia.routes.route import trivia


def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)
    app.config.from_object("config.DevelopmentConfig")
    database.init_db(app)
    migrate.init_app(app, database.db)
    Swagger(app)
    app.register_blueprint(trivia)

    if app.config["TESTING"]:
        app.config.from_object("config.TestingConfig")
        database.init_db(app)
        migrate.init_app(app, database.db)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
