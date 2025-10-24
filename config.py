import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8080"))
    use_sandbox: bool = os.getenv("USE_SANDBOX", "true").lower() == "true"
    token_sandbox: str | None = os.getenv("FREELANCER_SANDBOX_TOKEN")
    token_prod: str | None = os.getenv("FREELANCER_TOKEN")
    base_sandbox: str = os.getenv("FREELANCER_BASE_SANDBOX", "https://www.freelancer-sandbox.com/api")
    base_prod: str = os.getenv("FREELANCER_BASE_PROD", "https://www.freelancer.com/api")

    @property
    def base_url(self) -> str:
        return self.base_sandbox if self.use_sandbox else self.base_prod 
    
    @property
    def token(self) -> str | None:
        return self.token_sandbox if self.use_sandbox else self.token_prod