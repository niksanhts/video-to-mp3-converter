from dataclasses import dataclass
import environs


@dataclass
class Config:
    PROJECT_NAME: str
    RABBITMQ_HOST: str
    QUEUE_TO_SUBSCRIBE: str
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_DEFAULT_SENDER: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str

    DB_DRIVER: str     
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DATABASE_URL: str     


    @classmethod
    def load(cls):
        env = environs.Env()
        env.read_env()

        db_driver = env.str("DB_DRIVER", "mysql+pymysql")
        db_user = env("DB_USER")
        db_password = env("DB_PASSWORD")
        db_host = env.str("DB_HOST", "db")
        db_port = env.int("DB_PORT", 3306)
        db_name = env("DB_NAME")

        database_url = (
            f"{db_driver}://{db_user}:{db_password}"
            f"@{db_host}:{db_port}/{db_name}"
        )

        config = {
            "PROJECT_NAME": "Notification-Service",
            "RABBITMQ_HOST": env("RABBITMQ_HOST"),
            "QUEUE_TO_SUBSCRIBE": env("NOTIFICATION_QUEUE_TO_SUBSCRIBE"),
            "MAIL_SERVER": env.str("MAIL_SERVER", "smtp.mailtrap.io"),
            "MAIL_PORT": env.int("MAIL_PORT", 2525),
            "MAIL_DEFAULT_SENDER": "Notification-Service",
            "MAIL_USERNAME": env("MAIL_USERNAME"),
            "MAIL_PASSWORD": env("MAIL_PASSWORD"),

            "DB_DRIVER": db_driver,
            "DB_USER": db_user,
            "DB_PASSWORD": db_password,
            "DB_HOST": db_host,
            "DB_PORT": db_port,
            "DB_NAME": db_name,
            "DATABASE_URL": database_url,
        }
        return cls(**config)


settings = Config.load()
