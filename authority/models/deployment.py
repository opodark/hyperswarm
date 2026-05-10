from pydantic import BaseModel
from typing import Optional

class DeploymentModel(BaseModel):
    name: str
    method: str
    target: str
    model: Optional[str] = None
