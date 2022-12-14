import os
from os.path import dirname, join

from dotenv import load_dotenv

load_dotenv(join(dirname(__file__), ".env"))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN")
    API_AUDIENCE = os.environ.get("API_AUDIENCE")
    ALGORITHMS = os.getenv("ALGORITHMS")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    DEVELOPMENT = True
    ENV = "development"


class TestingConfig(Config):
    TESTING = True
    ENV = "testing"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_TEST_URL")
