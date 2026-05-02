from typing import Any

from pydantic import BaseModel, Field


class McpJsonSchema(BaseModel):
    type: str = "object"
    properties: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)
    additionalProperties: bool = False


class McpToolDescriptor(BaseModel):
    name: str
    description: str
    input_schema: McpJsonSchema
    output_schema: McpJsonSchema


class ToolCallRequest(BaseModel):
    name: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolError(BaseModel):
    code: str
    message: str
    backend_status: int | None = None
    detail: Any | None = None


class ToolCallResponse(BaseModel):
    ok: bool
    tool: str
    content: Any | None = None
    error: ToolError | None = None
