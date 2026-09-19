from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    dataset_path: str = r"C:\Users\redhi\OneDrive\Desktop\summer 2026\Dataset\Dataset"

    class Config:
        env_file = ".env"

settings = Settings()