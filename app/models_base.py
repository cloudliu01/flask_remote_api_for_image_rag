from pydantic import BaseModel, Field, validator
from datetime import datetime
import os
from typing import List

class ImageEntry(BaseModel):
    file_path: str
    user: str = Field(..., min_length=1)
    session: str = Field(..., min_length=1)

    @validator('URL')
    def validate_path_exists(cls, v):
        """Validator to ensure the path exists."""
        if not os.path.exists(v):
            raise ValueError(f"Path does not exist: {v}")
        return v

    class Config:
        """Pydantic configuration."""
        orm_mode = True
