import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


if load_dotenv:
    load_dotenv()


class Config:
    database_url = os.environ.get("DATABASE_URL")
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SECRET_KEY = os.environ.get("SECRET_KEY", "studenthome-cle-secrete-dev")
    SQLALCHEMY_DATABASE_URI = database_url or "sqlite:///" + os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "database.db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
