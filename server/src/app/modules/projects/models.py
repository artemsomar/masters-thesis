from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Project:
    id: str
    token_hash: str
    name: str
    document_xml: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
