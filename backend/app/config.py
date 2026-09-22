"""
config.py
Loads environment variables and exposes app-wide settings.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database — paste your Supabase connection string here as-is.
    # Find it in: Supabase dashboard -> Project Settings -> Database ->
    # Connection string -> URI. Both "postgresql://..." and
    # "postgresql+psycopg2://..." forms are accepted (see DATABASE_URL
    # property below, which normalizes it automatically).
    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:password@localhost:5432/postgres"
    )

    # JWT
    SECRET_KEY: str = "change_me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Admin self-registration — anyone creating an admin account via the
    # web form must know this key. Change it in .env for your deployment.
    ADMIN_REGISTRATION_KEY: str = "change_this_admin_key"

    # LLM fallback — called via the OpenAI SDK, but works with any
    # OpenAI-compatible provider. Defaults to Google Gemini's free tier
    # (no credit card needed) since OpenAI's API has no free tier.
    # Leave OPENAI_API_KEY blank (or set USE_LLM_FALLBACK=False) to
    # disable safely and run on rules only, with zero external calls.
    USE_LLM_FALLBACK: bool = True
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    OPENAI_MODEL: str = "gemini-2.5-flash"

    # App
    APP_NAME: str = "College Enquiry Chatbot"
    DEBUG: bool = True

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        """
        Normalizes the DATABASE_URL so you can paste Supabase's connection
        string exactly as given (which starts with "postgresql://") without
        needing to manually add the "+psycopg2" driver suffix SQLAlchemy
        requires.
        """
        url = self.DATABASE_URL.strip()
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgres://"):
            # Some tools (including older Supabase examples) use the
            # "postgres://" shorthand — SQLAlchemy requires "postgresql://".
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        return url

    class Config:
        env_file = ".env"


settings = Settings()
