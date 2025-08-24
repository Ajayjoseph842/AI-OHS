from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/hazero"
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    CORS_ORIGINS: str = "http://localhost:5173"

    OPENAI_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None
    RAG_PROVIDER: str = "local"  # local | pinecone | supabase


settings = Settings()