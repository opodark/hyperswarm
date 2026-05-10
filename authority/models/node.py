from pydantic import BaseModel
from typing import Optional, List

class NodeModel(BaseModel):
    node_id: str
    hostname: str
    role: str = "auto"
    model: Optional[str] = None
    capabilities: List[str] = []
