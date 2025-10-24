from typing import Literal, Optional
from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AuthStyle = Literal["bearer", "oauth", "api_key"]

class Settings(BaseSettings):
    # App
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8080, alias="APP_PORT")

    # Env switches
    use_sandbox: bool = Field(default=False, alias="USE_SANDBOX")
    auth_style: AuthStyle = Field(default="bearer", alias="FREELANCER_AUTH_STYLE")

    # Tokens
    token_sandbox: Optional[str] = Field(default=None, alias="FREELANCER_SANDBOX_TOKEN")
    token_prod: Optional[str] = Field(default=None, alias="FREELANCER_TOKEN")

    # Base URLs
    base_sandbox: str = Field(default="https://www.freelancer-sandbox.com/api", alias="FREELANCER_BASE_SANDBOX")
    base_prod: str = Field(default="https://www.freelancer.com/api", alias="FREELANCER_BASE_PROD")

    model_config = SettingsConfigDict(
        extra="ignore",
        # We load .env in main.py locally; on Cloud we rely on injected env.
        env_prefix="",  # read exact names
    )

    @field_validator("base_sandbox", "base_prod")
    @classmethod
    def _strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")

    @computed_field  # type: ignore[pydantic-computed-field]
    @property
    def token(self) -> Optional[str]:
        return self.token_sandbox if self.use_sandbox else self.token_prod

    @computed_field  # type: ignore[pydantic-computed-field]
    @property
    def base_url(self) -> str:
        return self.base_sandbox if self.use_sandbox else self.base_prod
