from pydantic import Extra
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Gateway-Service"

    USERS_SERVICE_URL: str
    MONGODB_URL: str
    RABBITMQ_HOST: str
    QUEUE_NAME: str
    FILE_STORAGE_URL : str = "http://file-storage-service:8020/files"

    class Config:
        extra = Extra.allow
        env_file = './.env'


settings = Settings()
