from pydantic import BaseModel

class BootstrapToken(BaseModel):
    token: str
    expires_at: str | None = None
