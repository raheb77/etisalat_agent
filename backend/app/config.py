from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "CSR Decision Support Backend"
    log_level: str = "INFO"


settings = Settings()
