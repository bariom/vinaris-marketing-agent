from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv(*_args: object, **_kwargs: object) -> bool:
        return False


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "posts.sqlite"
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE, override=False)


@dataclass(slots=True)
class Settings:
    app_name: str
    brand_name: str
    brand_payoff: str
    primary_language: str
    openai_api_key: str | None
    openai_image_model: str
    openai_image_quality: str
    openai_image_format: str
    database_path: Path
    generated_images_dir: Path
    web_secret_key: str
    beta_monthly_price: str
    beta_yearly_price: str
    beta_offer: str

    @property
    def has_openai_key(self) -> bool:
        return bool(self.openai_api_key)


def get_settings() -> Settings:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    database_path = Path(os.getenv("VINARIS_DB_PATH", str(DEFAULT_DB_PATH)))
    if not database_path.is_absolute():
        database_path = BASE_DIR / database_path

    return Settings(
        app_name="vinaris-marketing-agent",
        brand_name="Vinaris",
        brand_payoff="Private cellar intelligence",
        primary_language="it",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_image_model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2"),
        openai_image_quality=os.getenv("OPENAI_IMAGE_QUALITY", "medium"),
        openai_image_format=os.getenv("OPENAI_IMAGE_FORMAT", "png"),
        database_path=database_path,
        generated_images_dir=BASE_DIR / os.getenv("VINARIS_GENERATED_IMAGES_DIR", "generated_images"),
        web_secret_key=os.getenv("VINARIS_WEB_SECRET", "vinaris-marketing-agent-dev"),
        beta_monthly_price="CHF 6/mese",
        beta_yearly_price="CHF 60/anno",
        beta_offer="2 mesi gratuiti escluso AI Pack",
    )
