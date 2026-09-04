from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "CEA Ranking & Transaction Ingestion Engine"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite+aiosqlite:///./cea_engine.db"
    DATA_GOV_SG_API_URL: str = "https://data.gov.sg/api/action/datastore_search"
    CEA_SALESPERSON_RESOURCE_ID: str = "cea_salesperson_register"
    CEA_TRANSACTION_RESOURCE_ID: str = "cea_property_transactions"
    DEFAULT_TRAILING_MONTHS: int = 12
    PAGE_LIMIT_DEFAULT: int = 20
    PAGE_LIMIT_MAX: int = 100

    # Project directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    STATIC_DIR: Path = BASE_DIR / "app" / "static"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()
