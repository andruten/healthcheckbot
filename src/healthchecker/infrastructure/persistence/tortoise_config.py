import os

from dotenv import load_dotenv

load_dotenv()

TORTOISE_CONFIG = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.mysql",
            "credentials": {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", "3306")),
                "user": os.getenv("DB_USER", "healthchecker"),
                "password": os.getenv("DB_PASSWORD", "healthchecker"),
                "database": os.getenv("DB_NAME", "healthchecker"),
                "minsize": 1,
                "maxsize": 5,
            },
        },
    },
    "apps": {
        "models": {
            "models": [
                "healthchecker.infrastructure.persistence.tortoise_models",
            ],
            "default_connection": "default",
        },
    },
}
