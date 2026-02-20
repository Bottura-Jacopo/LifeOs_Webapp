from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://lifeos:lifeos@localhost:5432/lifeos"


settings = Settings()