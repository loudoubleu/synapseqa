from typing import Literal

from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="TEST_", extra="ignore")

    env: Literal["local", "demo"] = "local"
    orangehrm_url: HttpUrl = HttpUrl("http://localhost:8081")
    admin_username: str
    admin_password: SecretStr
    booker_api_url: HttpUrl = HttpUrl("https://restful-booker.herokuapp.com")
    default_timeout_ms: int = 10_000

    @property
    def is_shared_env(self) -> bool:
        return self.env == "demo"
