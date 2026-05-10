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

    _secret = os.environ.get("SECRET_KEY")
    if not _secret:
        import warnings
        warnings.warn(
            "SECRET_KEY is not set — using insecure default. Set SECRET_KEY env var in production.",
            stacklevel=2,
        )
    SECRET_KEY = _secret or "studenthome-cle-secrete-dev-CHANGEME"
    SQLALCHEMY_DATABASE_URI = database_url or "sqlite:///" + os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "database.db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
