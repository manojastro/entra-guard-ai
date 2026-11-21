from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateServiceNowRequest(BaseModel):
    assignment_group: str | None = Field(default=None, max_length=160)
    short_description: str | None = Field(default=None, max_length=160)
    description: str | None = Field(default=None, max_length=12000)


class UpdateServiceNowRequest(BaseModel):
    status: str | None = Field(default=None, max_length=40)
    assignment_group: str | None = Field(default=None, max_length=160)
    short_description: str | None = Field(default=None, max_length=160)


class CommentRequest(BaseModel):
    comment: str = Field(min_length=1, max_length=8000)


class IncidentStatusRequest(BaseModel):
    status: str = Field(pattern="^(Open|Investigating|Resolved|Closed)$")


class ApiError(BaseModel):
    detail: str
    retryable: bool = False


JsonDict = dict[str, Any]

