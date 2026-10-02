"""Typed shapes for login and the few writes the console allows."""
from typing import Literal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=200)
    remember: bool = False


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: str  # admin, employee or customer
    home: str  # where this person lands after signing in


class RiskStatusUpdate(BaseModel):
    status: Literal["open", "acknowledged", "resolved"]
