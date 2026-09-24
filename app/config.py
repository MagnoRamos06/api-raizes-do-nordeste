from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/raizes.db"
    jwt_secret_key: str = Field(min_length=32)
    seed_admin_email: str = ""
    seed_admin_password: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
