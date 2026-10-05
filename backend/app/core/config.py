import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://sentinel:sentinel@localhost:5432/sentinel",
)