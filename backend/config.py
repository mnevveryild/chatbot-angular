import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} tam sayi olmalidir.") from exc


@dataclass(frozen=True)
class Settings:
    llm_timeout_seconds: int = _get_int("LLM_TIMEOUT_SECONDS", 120)

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    mysql_uri: str = os.getenv(
        "MYSQL_URI",
        "mysql+pymysql://kullanici:sifre@localhost:3306/veritabani",
    )

    database_url: str = os.getenv(
        "DATABASE_URL",
        os.getenv(
            "MYSQL_URI",
            "mysql+pymysql://kullanici:sifre@localhost:3306/veritabani",
        ),
    )

settings = Settings()
