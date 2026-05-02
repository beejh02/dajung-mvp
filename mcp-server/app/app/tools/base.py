from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.backend_client import BackendClient
from app.schemas import McpJsonSchema, McpToolDescriptor


ToolHandler = Callable[[dict[str, Any], "ToolContext"], Any]


@dataclass(frozen=True)
class ToolContext:
    backend: BackendClient
    access_token: str | None


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: McpJsonSchema
    output_schema: McpJsonSchema
    handler: ToolHandler

    def descriptor(self) -> McpToolDescriptor:
        return McpToolDescriptor(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
        )
