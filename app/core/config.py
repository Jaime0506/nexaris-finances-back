from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Nexaris Finance Back"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "API for the Nexaris Finance Backend"
    APP_PREFIX: str = "/api/v1"
    APP_DOCS_URL: str = "/docs"

    # Defino las variables que va a tener mi .env
    PG_HOST: str
    PG_DATABASE: str
    PG_USER: str
    PG_PASSWORD: str
    PG_SSLMODE: str = 'require'
    PG_CHANNELBINDING: str = 'require'
    PG_PORT: int = 5432
    PG_SCHEMA: str = 'sys'

    class Config:
        env_file = Path(__file__).resolve().parent.parent.parent / ".env"

    @property
    def get_db_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.PG_USER}:{self.PG_PASSWORD}"
            f"@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DATABASE}"
        )


settings = Settings()
# print(settings.APP_NAME)