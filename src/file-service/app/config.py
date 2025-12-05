import os
from pydantic import BaseSettings, AnyUrl, Field


class Settings(BaseSettings):
    MONGODB_URL: AnyUrl = Field(..., env="MONGODB_URL")

    class Config:
        env_file = ".env"


settings = Settings()
