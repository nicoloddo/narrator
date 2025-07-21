from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from .narrator_mode import NarratorMode


class RecordModel(BaseModel):
    """Model for records received from the database queue."""

    id: str = Field(..., description="Unique identifier for the record")
    mode: NarratorMode = Field(..., description="The narrator mode to use")
    content: Optional[str] = Field(None, description="Content/message from the user")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )

    class Config:
        use_enum_values = True
        extra = "allow"  # Allow additional fields that might come from the queue
