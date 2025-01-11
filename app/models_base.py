from pydantic import BaseModel, Field, validator
from datetime import datetime
import os
from typing import List

class ImageEntry(BaseModel):
    dir_path: str
    user: str = Field(..., min_length=1)
    session: str = Field(..., min_length=1)

    @validator('dir_path')
    def validate_path_exists(cls, v):
        """Validator to ensure the path exists."""
        if not os.path.exists(v):
            raise ValueError(f"Path does not exist: {v}")
        return v

    class Config:
        """Pydantic configuration."""
        orm_mode = True

        

# Define the JSON schema for API process_chat_json
ChatJsonSchema = {
    "type": "object",
    "properties": {
        "model": {"type": "string"},
        "user": {"type": "string"},
        "session": {"type": "string"},
        "stream": {"type": "boolean"},
        "messages": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "role": {"type": "string"},
                    "content": {
                        "oneOf": [
                            {"type": "string"},
                            {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"type": "string"},
                                        "text": {"type": "string"},
                                        "image_url": {
                                            "type": "object",
                                            "properties": {
                                                "url": {"type": "string"},
                                                "detail": {"type": "string"}
                                            },
                                            "required": ["url", "detail"]
                                        },
                                        "location": {
                                            "type": "object",
                                            "properties": {
                                                "longitude": {"type": "number"},
                                                "latitude": {"type": "number"}
                                            },
                                            "required": ["longitude", "latitude"]
                                        }
                                    },
                                    "required": ["type"]
                                }
                            },
                            {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string"},
                                    "location": {
                                        "type": "object",
                                        "properties": {
                                            "longitude": {"type": "number"},
                                            "latitude": {"type": "number"}
                                        },
                                        "required": ["longitude", "latitude"]
                                    }
                                },
                                "required": ["type", "location"]
                            }
                        ]
                    }
                },
                "required": ["role", "content"]
            }
        },
        "max_tokens": {"type": "integer"}
    },
    "required": ["model", "user", "session", "stream", "messages", "max_tokens"]
}
