import os
from pathlib import Path

from pydantic import BaseModel


BACKEND_ENV_FILE = Path(__file__).resolve().parents[1] / ".env.local"


def _strip_wrapping_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _load_env_local(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        env_key = key.strip()
        if not env_key or env_key in os.environ:
            continue
        os.environ[env_key] = _strip_wrapping_quotes(value.strip())


_load_env_local(BACKEND_ENV_FILE)


class Settings(BaseModel):
    app_name: str = "CSR Decision Support Backend"
    log_level: str = "INFO"
    llm_provider: str = os.getenv("LLM_PROVIDER", "local")
    llm_model: str = os.getenv("LLM_MODEL", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")
    kimi_api_key: str = os.getenv("KIMI_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    ssl_cert_file: str = os.getenv("SSL_CERT_FILE", "")
    llm_timeout_seconds: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))


settings = Settings()
